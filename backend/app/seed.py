"""Insert the 5 dining halls. Safe to run repeatedly.

Run: docker compose exec backend python -m app.seed
"""

import asyncio

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from app.db.session import SessionLocal, engine
from app.models import Venue

# Hard-coded for v1 (DECISIONS #9).
# TODO: coordinates are approximate — verify each one on Google Maps.
VENUES = [
    {"name": "Chenango Champlain Collegiate Center (C4)", "lat": 42.0873, "lng": -75.9640},
    {"name": "Appalachian Collegiate Center", "lat": 42.0930, "lng": -75.9750},
    {"name": "Hinman Dining", "lat": 42.0925, "lng": -75.9685},
    {"name": "Marché (College-in-the-Woods)", "lat": 42.0862, "lng": -75.9738},
    {"name": "Café Tempo", "lat": 42.0890, "lng": -75.9695},
]


async def seed() -> None:
    async with SessionLocal() as session:
        # ON CONFLICT DO NOTHING relies on the unique constraint on venues.name
        stmt = insert(Venue).values(VENUES).on_conflict_do_nothing(index_elements=["name"])
        result = await session.execute(stmt)
        await session.commit()

        total = await session.scalar(select(func.count()).select_from(Venue))
        print(f"Inserted {result.rowcount} new venue(s). Total venues: {total}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
