"""Insert or update the dining halls. Safe to run repeatedly.

Run: docker compose exec backend python -m app.seed
"""

import asyncio

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from app.db.session import SessionLocal, engine
from app.models import Venue

# Hard-coded for v1 (DECISIONS #9). Coordinates taken from Google Maps.
# Keep this order: it decides the ids (1–4) on a fresh database.
VENUES = [
    {"name": "Chenango Champlain Collegiate Center (C4)", "lat": 42.08801694110123, "lng": -75.96314617033673},
    {"name": "Appalachian Collegiate Center", "lat": 42.08575280503048, "lng": -75.96957153827712},
    {"name": "Hinman Dining", "lat": 42.08643873907953, "lng": -75.97271494875632},
    {"name": "Marché (College-in-the-Woods)", "lat": 42.08593198571488, "lng": -75.96644718627341},
]


async def seed() -> None:
    async with SessionLocal() as session:
        # Upsert on the unique name: new halls are inserted, existing ones get
        # the latest coordinates. Halls removed from VENUES are NOT deleted here
        # (that would cascade-delete their reports) — remove those by hand.
        stmt = insert(Venue).values(VENUES)
        stmt = stmt.on_conflict_do_update(
            index_elements=["name"],
            set_={"lat": stmt.excluded.lat, "lng": stmt.excluded.lng},
        )
        await session.execute(stmt)
        await session.commit()

        total = await session.scalar(select(func.count()).select_from(Venue))
        print(f"Upserted {len(VENUES)} venue(s). Total venues: {total}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
