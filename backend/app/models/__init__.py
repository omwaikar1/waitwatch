# Import every model here so `import app.models` registers all tables on Base.metadata
from app.models.venue import Venue
from app.models.venue_stats import VenueStats
from app.models.wait_report import WaitReport

__all__ = ["Venue", "VenueStats", "WaitReport"]
