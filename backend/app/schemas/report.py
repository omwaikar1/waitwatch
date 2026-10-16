import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReportCreate(BaseModel):
    """Request body for POST /venues/{venue_id}/reports."""

    device_id: uuid.UUID
    # Same 0–120 rule as the DB CHECK constraint, so bad input gets a 422 first
    wait_minutes: int = Field(ge=0, le=120)


class ReportOut(BaseModel):
    """A saved report. device_id is deliberately not sent back."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    venue_id: int
    wait_minutes: int
    created_at: datetime
