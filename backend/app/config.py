from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Reads real environment variables first, then falls back to backend/.env
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # No defaults: the app refuses to start if either is missing
    DATABASE_URL: str
    REDIS_URL: str

    # Tunables (DECISIONS #22). Defaults are the agreed values; override via env to test.
    CACHE_TTL_SECONDS: int = 300  # how long GET /venues stays cached (DECISIONS #4)
    STALE_AFTER_MINUTES: int = 45  # reports older than this stop counting (DECISIONS #6)
    EXPIRE_JOB_INTERVAL_MINUTES: int = 15  # how often the stale job runs (DECISIONS #5)
    REPORT_COOLDOWN_SECONDS: int = 600  # one report per device per venue per window


# Created once at import time; everything else does `from app.config import settings`
settings = Settings()
