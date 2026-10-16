from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# One engine for the whole app; it owns the connection pool
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # test a pooled connection before using it, drop it if dead
)

# Factory that creates a new session each time it's called
SessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,  # keep loaded objects usable after commit (needed in async)
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: one session per request, always closed afterwards."""
    async with SessionLocal() as session:
        yield session
