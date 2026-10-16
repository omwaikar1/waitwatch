from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import Venue, WaitReport
from app.schemas import ReportCreate, ReportOut, VenueOut

router = APIRouter(prefix="/venues", tags=["venues"])

# Reports older than this don't count (DECISIONS #6). Filtered at read time
# until the stale-report job exists (Step 9).
FRESH_WINDOW = timedelta(minutes=45)


@router.get("", response_model=list[VenueOut])
async def list_venues(db: AsyncSession = Depends(get_db)):
    # Average + count of fresh reports per venue
    fresh = (
        select(
            WaitReport.venue_id,
            func.avg(WaitReport.wait_minutes).label("avg_wait"),
            func.count().label("report_count"),
        )
        .where(
            WaitReport.is_stale.is_(False),
            WaitReport.created_at > func.now() - FRESH_WINDOW,
        )
        .group_by(WaitReport.venue_id)
        .subquery()
    )

    # LEFT JOIN keeps venues that have no fresh reports
    stmt = (
        select(Venue, fresh.c.avg_wait, fresh.c.report_count)
        .outerjoin(fresh, fresh.c.venue_id == Venue.id)
        .order_by(Venue.id)
    )
    rows = (await db.execute(stmt)).all()

    return [
        VenueOut(
            id=venue.id,
            name=venue.name,
            lat=venue.lat,
            lng=venue.lng,
            avg_wait_minutes=round(float(avg), 1) if avg is not None else None,
            report_count=count or 0,
        )
        for venue, avg, count in rows
    ]


@router.post(
    "/{venue_id}/reports",
    response_model=ReportOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_report(
    venue_id: int,
    report: ReportCreate,
    db: AsyncSession = Depends(get_db),
):
    if await db.get(Venue, venue_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venue not found")

    new_report = WaitReport(venue_id=venue_id, **report.model_dump())
    db.add(new_report)
    await db.commit()
    await db.refresh(new_report)  # load server-generated id and created_at
    return new_report
