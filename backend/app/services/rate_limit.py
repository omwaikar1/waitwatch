"""One report per device per venue per cooldown window (DECISIONS #21)."""

import logging
import uuid

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.config import settings

logger = logging.getLogger(__name__)


async def check_report_allowed(redis: Redis, device_id: uuid.UUID, venue_id: int) -> int | None:
    """Return None if allowed, or the seconds left to wait if blocked."""
    key = f"ratelimit:{device_id}:{venue_id}"
    try:
        # Atomic: only one request can create the key, so two at once can't both pass
        created = await redis.set(key, 1, nx=True, ex=settings.REPORT_COOLDOWN_SECONDS)
        if created:
            return None
        return max(await redis.ttl(key), 1)
    except RedisError as exc:
        # Fail open: losing spam protection briefly beats rejecting real reports (DECISIONS #19)
        logger.warning("Redis unavailable (%s); skipping rate limit for %s", exc, key)
        return None
