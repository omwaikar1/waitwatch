from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.redis import get_redis
from app.db.session import get_db
from app.schemas import ReportCreate, ReportOut, VenueOut
from app.services import venue_service
from app.services.rate_limit import check_report_allowed
from app.services.venue_service import VenueNotFound

router = APIRouter(prefix="/venues", tags=["venues"])


@router.get("", response_model=list[VenueOut])
async def list_venues(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    return await venue_service.list_venues(db, redis)


@router.post(
    "/{venue_id}/reports",
    response_model=ReportOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_report(
    venue_id: int,
    report: ReportCreate,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    # Checked before touching Postgres, so blocked requests cost almost nothing
    retry_after = await check_report_allowed(redis, report.device_id, venue_id)
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="You already reported this venue recently",
            headers={"Retry-After": str(retry_after)},
        )

    try:
        return await venue_service.create_report(db, redis, venue_id, report)
    except VenueNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venue not found")
