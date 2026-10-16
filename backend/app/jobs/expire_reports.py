import logging
from datetime import timedelta

from sqlalchemy import func, update
from sqlalchemy.dialects.postgresql import insert

from app.config import settings
from app.db.redis import redis_client
from app.db.session import SessionLocal
from app.models import VenueStats, WaitReport
from app.services.venue_service import compute_venue_stats, invalidate_venues_cache

logger = logging.getLogger(__name__)


async def expire_stale_reports() -> None:
    """Mark old reports stale, snapshot every venue's average, clear the cache."""
    # No request here, so no get_db(): the job opens its own session
    async with SessionLocal() as db:
        # 1. Soft-delete: flip is_stale, never delete rows (DECISIONS #6)
        result = await db.execute(
            update(WaitReport)
            .where(
                WaitReport.is_stale.is_(False),
                WaitReport.created_at
                < func.now() - timedelta(minutes=settings.STALE_AFTER_MINUTES),
            )
            .values(is_stale=True)
        )
        marked = result.rowcount

        # 2. Snapshot current averages into venue_stats (DECISIONS #20)
        venues = await compute_venue_stats(db)
        if venues:
            stmt = insert(VenueStats).values(
                [
                    {
                        "venue_id": v.id,
                        "avg_wait_minutes": v.avg_wait_minutes,
                        "report_count": v.report_count,
                    }
                    for v in venues
                ]
            )
            # Upsert: insert a row per venue, or update the one that's already there
            stmt = stmt.on_conflict_do_update(
                index_elements=[VenueStats.venue_id],
                set_={
                    "avg_wait_minutes": stmt.excluded.avg_wait_minutes,
                    "report_count": stmt.excluded.report_count,
                    "updated_at": func.now(),
                },
            )
            await db.execute(stmt)

        await db.commit()

    # 3. Averages may have changed, so drop the cached list
    await invalidate_venues_cache(redis_client)
    logger.info("Expire job: marked %d stale, refreshed %d venue_stats", marked, len(venues))
