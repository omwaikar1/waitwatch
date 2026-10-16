from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Reads real environment variables first, then falls back to backend/.env
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # No defaults: the app refuses to start if either is missing
    DATABASE_URL: str
    REDIS_URL: str


# Created once at import time; everything else does `from app.config import settings`
settings = Settings()
