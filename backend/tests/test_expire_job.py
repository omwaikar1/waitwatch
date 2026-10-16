"""The background job: mark stale, snapshot venue_stats, clear cache."""

from sqlalchemy import select

from app.jobs.expire_reports import expire_stale_reports
from app.models import VenueStats, WaitReport
from app.services.venue_service import VENUES_CACHE_KEY


async def test_marks_only_old_reports_stale(db, add_report):
    fresh = await add_report(minutes=10, age_minutes=5)
    old = await add_report(minutes=50, age_minutes=60)

    await expire_stale_reports()  # changes rows through its OWN session

    # Our session still holds the old in-memory copies; forget them and re-read
    db.expire_all()
    rows = {r.id: r.is_stale for r in (await db.execute(select(WaitReport))).scalars()}
    assert rows == {fresh.id: False, old.id: True}  # flipped, never deleted


async def test_writes_one_stats_row_per_venue(db, add_report):
    await add_report(venue_id=1, minutes=15)
    await add_report(venue_id=1, minutes=25)

    await expire_stale_reports()

    stats = {s.venue_id: s for s in (await db.execute(select(VenueStats))).scalars()}
    assert len(stats) == 5
    assert (stats[1].avg_wait_minutes, stats[1].report_count) == (20.0, 2)
    assert stats[2].avg_wait_minutes is None


async def test_running_twice_updates_instead_of_duplicating(db, add_report):
    await expire_stale_reports()
    await add_report(venue_id=1, minutes=40)

    await expire_stale_reports()  # upsert: same 5 rows, new values

    stats = (await db.execute(select(VenueStats))).scalars().all()
    assert len(stats) == 5
    assert next(s for s in stats if s.venue_id == 1).avg_wait_minutes == 40.0


async def test_clears_the_cache(redis):
    await redis.set(VENUES_CACHE_KEY, "old value")

    await expire_stale_reports()

    assert not await redis.exists(VENUES_CACHE_KEY)
