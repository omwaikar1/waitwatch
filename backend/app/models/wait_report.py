import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WaitReport(Base):
    """One wait time submitted by one device. Raw data — never hard-deleted."""

    __tablename__ = "wait_reports"
    __table_args__ = (
        CheckConstraint("wait_minutes BETWEEN 0 AND 120", name="wait_minutes_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    venue_id: Mapped[int] = mapped_column(
        ForeignKey("venues.id", ondelete="CASCADE"), index=True
    )
    device_id: Mapped[uuid.UUID]
    wait_minutes: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    # Flipped to true by the expiry job after 45 min (DECISIONS #6)
    is_stale: Mapped[bool] = mapped_column(default=False, server_default="false")

    venue: Mapped["Venue"] = relationship(back_populates="reports")
