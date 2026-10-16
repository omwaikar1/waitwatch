from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Venue(Base):
    """A dining hall. The 5 halls are inserted by app/seed.py."""

    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    # Plain floats instead of PostGIS (DECISIONS #9)
    lat: Mapped[float]
    lng: Mapped[float]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    reports: Mapped[list["WaitReport"]] = relationship(back_populates="venue")
    stats: Mapped["VenueStats | None"] = relationship(back_populates="venue")
