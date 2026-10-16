from pydantic import BaseModel, ConfigDict


class VenueOut(BaseModel):
    """A dining hall as returned by GET /venues, with its live average."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    lat: float
    lng: float
    avg_wait_minutes: float | None  # None when there are no fresh reports
    report_count: int
