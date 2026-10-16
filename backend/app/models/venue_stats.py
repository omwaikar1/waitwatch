from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class VenueStats(Base):
    """Last computed average per venue. Durable copy of what Redis caches."""

    __tablename__ = "venue_stats"

    # Primary key is also the foreign key: at most one stats row per venue
    venue_id: Mapped[int] = mapped_column(
        ForeignKey("venues.id", ondelete="CASCADE"), primary_key=True
    )
    avg_wait_minutes: Mapped[float | None]  # None when there are no fresh reports
    report_count: Mapped[int] = mapped_column(default=0, server_default="0")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    venue: Mapped["Venue"] = relationship(back_populates="stats")
