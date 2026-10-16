"""Service layer: averages, freshness, caching, creating reports."""

import uuid

import pytest
from redis.asyncio import Redis
from sqlalchemy import select

from app.models import WaitReport
from app.schemas import ReportCreate
from app.seed import VENUES
from app.services import venue_service
from app.services.venue_service import VENUES_CACHE_KEY, VenueNotFound


def by_id(venues, venue_id):
    return next(v for v in venues if v.id == venue_id)


# ── compute_venue_stats: the averaging rules ──


async def test_every_venue_listed_with_no_reports(db):
    venues = await venue_service.compute_venue_stats(db)

    assert len(venues) == len(VENUES)
    assert all(v.avg_wait_minutes is None and v.report_count == 0 for v in venues)


async def test_average_of_fresh_reports(db, add_report):
    await add_report(venue_id=1, minutes=15)
    await add_report(venue_id=1, minutes=25)

    c4 = by_id(await venue_service.compute_venue_stats(db), 1)

    assert c4.avg_wait_minutes == 20.0
    assert c4.report_count == 2


async def test_average_rounded_to_one_decimal(db, add_report):
    for minutes in (10, 10, 11):  # 31 / 3 = 10.333…
        await add_report(venue_id=1, minutes=minutes)

    assert by_id(await venue_service.compute_venue_stats(db), 1).avg_wait_minutes == 10.3


async def test_reports_older_than_45_minutes_ignored(db, add_report):
    await add_report(venue_id=1, minutes=20, age_minutes=10)
    await add_report(venue_id=1, minutes=100, age_minutes=60)

    c4 = by_id(await venue_service.compute_venue_stats(db), 1)

    assert c4.avg_wait_minutes == 20.0
    assert c4.report_count == 1


async def test_stale_reports_ignored_even_if_recent(db, add_report):
    await add_report(venue_id=1, minutes=20)
    await add_report(venue_id=1, minutes=100, stale=True)

    assert by_id(await venue_service.compute_venue_stats(db), 1).avg_wait_minutes == 20.0


async def test_reports_only_count_for_their_own_venue(db, add_report):
    await add_report(venue_id=1, minutes=30)

    venues = await venue_service.compute_venue_stats(db)

    assert by_id(venues, 1).report_count == 1
    assert by_id(venues, 2).report_count == 0


# ── list_venues: cache-aside ──


async def test_list_venues_stores_result_in_cache(db, redis):
    await venue_service.list_venues(db, redis)

    assert await redis.exists(VENUES_CACHE_KEY)
    assert 0 < await redis.ttl(VENUES_CACHE_KEY) <= 300


async def test_list_venues_served_from_cache_on_hit(db, redis, add_report):
    await venue_service.list_venues(db, redis)  # miss → caches "no reports"
    await add_report(venue_id=1, minutes=30)  # DB changes behind the cache's back

    cached = await venue_service.list_venues(db, redis)  # hit → still the old answer

    assert by_id(cached, 1).report_count == 0


async def test_list_venues_works_when_redis_is_down(db, add_report):
    await add_report(venue_id=1, minutes=12)
    dead_redis = Redis.from_url("redis://localhost:1/0", socket_connect_timeout=0.5)

    venues = await venue_service.list_venues(db, dead_redis)  # must not raise

    assert by_id(venues, 1).avg_wait_minutes == 12.0
    await dead_redis.aclose()


# ── create_report ──


async def test_create_report_saves_row(db, redis):
    device = uuid.uuid4()

    report = await venue_service.create_report(
        db, redis, 1, ReportCreate(device_id=device, wait_minutes=15)
    )

    assert report.id is not None and report.created_at is not None
    saved = (await db.execute(select(WaitReport))).scalar_one()
    assert (saved.venue_id, saved.device_id, saved.wait_minutes) == (1, device, 15)


async def test_create_report_invalidates_cache(db, redis):
    await venue_service.list_venues(db, redis)
    assert await redis.exists(VENUES_CACHE_KEY)

    await venue_service.create_report(
        db, redis, 1, ReportCreate(device_id=uuid.uuid4(), wait_minutes=15)
    )

    assert not await redis.exists(VENUES_CACHE_KEY)
    # …so the next read sees the new report
    assert by_id(await venue_service.list_venues(db, redis), 1).report_count == 1


async def test_create_report_unknown_venue_raises(db, redis):
    with pytest.raises(VenueNotFound):
        await venue_service.create_report(
            db, redis, 999, ReportCreate(device_id=uuid.uuid4(), wait_minutes=15)
        )
