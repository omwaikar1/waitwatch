"""Business logic for venues and reports. No HTTP here (DECISIONS #7)."""

import logging
from datetime import timedelta

from pydantic import TypeAdapter
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Venue, WaitReport
from app.schemas import ReportCreate, VenueOut

logger = logging.getLogger(__name__)

VENUES_CACHE_KEY = "venues:all"
_venue_list = TypeAdapter(list[VenueOut])  # converts list[VenueOut] <-> JSON


class VenueNotFound(Exception):
    """Raised when a venue id doesn't exist. The route turns it into a 404."""


async def compute_venue_stats(db: AsyncSession) -> list[VenueOut]:
    """Live average + count of fresh reports for every venue (source of truth)."""
    fresh = (
        select(
            WaitReport.venue_id,
            func.avg(WaitReport.wait_minutes).label("avg_wait"),
            func.count().label("report_count"),
        )
        .where(
            WaitReport.is_stale.is_(False),
            WaitReport.created_at
            > func.now() - timedelta(minutes=settings.STALE_AFTER_MINUTES),
        )
        .group_by(WaitReport.venue_id)
        .subquery()
    )

    # LEFT JOIN keeps venues that have no fresh reports
    stmt = (
        select(Venue, fresh.c.avg_wait, fresh.c.report_count)
        .outerjoin(fresh, fresh.c.venue_id == Venue.id)
        .order_by(Venue.id)
    )
    rows = (await db.execute(stmt)).all()

    return [
        VenueOut(
            id=venue.id,
            name=venue.name,
            lat=venue.lat,
            lng=venue.lng,
            avg_wait_minutes=round(float(avg), 1) if avg is not None else None,
            report_count=count or 0,
        )
        for venue, avg, count in rows
    ]


async def list_venues(db: AsyncSession, redis: Redis) -> list[VenueOut]:
    """Cache-aside: try Redis, otherwise compute from Postgres and cache the result."""
    try:
        cached = await redis.get(VENUES_CACHE_KEY)
        if cached is not None:
            return _venue_list.validate_json(cached)
    except RedisError as exc:
        logger.warning("Redis unavailable on read (%s); falling back to Postgres", exc)

    venues = await compute_venue_stats(db)

    try:
        await redis.set(
            VENUES_CACHE_KEY, _venue_list.dump_json(venues), ex=settings.CACHE_TTL_SECONDS
        )
    except RedisError as exc:
        logger.warning("Redis unavailable (%s); result not cached", exc)

    return venues


async def invalidate_venues_cache(redis: Redis) -> None:
    """Delete the cached list so the next GET recomputes it. Never raises."""
    try:
        await redis.delete(VENUES_CACHE_KEY)
    except RedisError as exc:
        # Worst case the cache is stale until its TTL expires
        logger.warning("Redis unavailable (%s); could not invalidate %s", exc, VENUES_CACHE_KEY)


async def create_report(
    db: AsyncSession, redis: Redis, venue_id: int, data: ReportCreate
) -> WaitReport:
    if await db.get(Venue, venue_id) is None:
        raise VenueNotFound(venue_id)

    report = WaitReport(venue_id=venue_id, **data.model_dump())
    db.add(report)
    await db.commit()
    await db.refresh(report)  # load server-generated id and created_at

    await invalidate_venues_cache(redis)
    return report
