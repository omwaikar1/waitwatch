"""Shared test setup. pytest loads this file before any test module."""

import os

# ── 1. Point the app at TEST resources before anything imports app.config ──
# Settings() is created at import time, so these must be set first.
_db_base, _real_db_name = os.environ["DATABASE_URL"].rsplit("/", 1)
os.environ["DATABASE_URL"] = f"{_db_base}/waitwatch_test"
os.environ["REDIS_URL"] = os.environ["REDIS_URL"].rsplit("/", 1)[0] + "/15"

import asyncio  # noqa: E402
import uuid  # noqa: E402
from datetime import timedelta  # noqa: E402

import httpx  # noqa: E402
import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy import func, insert, text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

from app.db.redis import redis_client  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Venue, WaitReport  # noqa: E402
from app.seed import VENUES  # noqa: E402


# ── 2. Once per test run: create the test DB and build it with real migrations ──
async def _create_test_database() -> None:
    admin = create_async_engine(f"{_db_base}/postgres", isolation_level="AUTOCOMMIT")
    async with admin.connect() as conn:
        exists = await conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = 'waitwatch_test'")
        )
        if not exists:
            await conn.execute(text("CREATE DATABASE waitwatch_test"))
    await admin.dispose()


@pytest.fixture(scope="session", autouse=True)
def test_database():
    assert "waitwatch_test" in os.environ["DATABASE_URL"]  # never touch the real DB
    asyncio.run(_create_test_database())
    cfg = Config("alembic.ini")
    command.downgrade(cfg, "base")  # start from nothing every run
    command.upgrade(cfg, "head")  # same migrations as production
    yield


# ── 3. Before every test: empty tables, 5 fresh halls, empty Redis ──
@pytest.fixture(autouse=True)
async def clean_state():
    async with engine.begin() as conn:
        await conn.execute(
            text("TRUNCATE wait_reports, venue_stats, venues RESTART IDENTITY CASCADE")
        )
        await conn.execute(insert(Venue), VENUES)
    await redis_client.flushdb()
    yield
    # Each test gets its own event loop; drop connections tied to this one
    await engine.dispose()
    await redis_client.connection_pool.disconnect()


# ── 4. Fixtures tests can ask for by name ──
@pytest.fixture
async def db():
    async with SessionLocal() as session:
        yield session


@pytest.fixture
def redis():
    return redis_client


@pytest.fixture
async def client():
    """HTTP client that calls the FastAPI app in-process (no real network)."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def add_report(db):
    """Insert a report directly. Lets tests create old or stale reports."""

    async def _add(venue_id=1, minutes=10, age_minutes=0, stale=False, device_id=None):
        report = WaitReport(
            venue_id=venue_id,
            device_id=device_id or uuid.uuid4(),
            wait_minutes=minutes,
            is_stale=stale,
            created_at=func.now() - timedelta(minutes=age_minutes),
        )
        db.add(report)
        await db.commit()
        return report

    return _add
