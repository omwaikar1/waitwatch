"""Rate limiting: 1 report per device per venue per cooldown."""

import asyncio
import uuid

from redis.asyncio import Redis

from app.services.rate_limit import check_report_allowed


async def test_first_report_allowed(redis):
    assert await check_report_allowed(redis, uuid.uuid4(), 1) is None


async def test_second_report_blocked_with_seconds_to_wait(redis):
    device = uuid.uuid4()
    await check_report_allowed(redis, device, 1)

    retry_after = await check_report_allowed(redis, device, 1)

    assert retry_after is not None and 0 < retry_after <= 600


async def test_same_device_can_report_a_different_venue(redis):
    device = uuid.uuid4()
    await check_report_allowed(redis, device, 1)

    assert await check_report_allowed(redis, device, 2) is None


async def test_different_device_can_report_same_venue(redis):
    await check_report_allowed(redis, uuid.uuid4(), 1)

    assert await check_report_allowed(redis, uuid.uuid4(), 1) is None


async def test_simultaneous_requests_only_one_allowed(redis):
    """The race-condition test: SET NX is atomic, so exactly one wins."""
    device = uuid.uuid4()

    results = await asyncio.gather(*(check_report_allowed(redis, device, 1) for _ in range(10)))

    assert results.count(None) == 1


async def test_allowed_when_redis_is_down():
    dead_redis = Redis.from_url("redis://localhost:1/0", socket_connect_timeout=0.5)

    assert await check_report_allowed(dead_redis, uuid.uuid4(), 1) is None  # fail open
    await dead_redis.aclose()
