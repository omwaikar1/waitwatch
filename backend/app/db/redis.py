from redis.asyncio import Redis

from app.config import settings

# One client for the whole app; it keeps its own connection pool (like the DB engine)
redis_client: Redis = Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,  # return str instead of bytes
    socket_connect_timeout=1,  # if Redis is down, give up fast and fall back (DECISIONS #19)
    socket_timeout=1,
)


async def get_redis() -> Redis:
    """FastAPI dependency: the shared Redis client."""
    return redis_client
