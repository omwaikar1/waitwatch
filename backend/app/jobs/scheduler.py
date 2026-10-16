from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.jobs.expire_reports import expire_stale_reports

# Runs inside the FastAPI process on the same event loop (DECISIONS #5)
scheduler = AsyncIOScheduler(timezone="UTC")

scheduler.add_job(
    expire_stale_reports,
    trigger="interval",
    minutes=settings.EXPIRE_JOB_INTERVAL_MINUTES,
    next_run_time=datetime.now(timezone.utc),  # also run once right at startup
    id="expire_stale_reports",
    max_instances=1,  # never overlap with itself if a run is slow
    coalesce=True,  # if runs were missed, do one catch-up run, not many
)
