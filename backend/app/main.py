import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.redis import redis_client
from app.db.session import engine
from app.jobs.scheduler import scheduler
from app.routes import venues

logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(name)s - %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: begin background jobs
    scheduler.start()
    yield
    # Shutdown: stop jobs first, then close connections cleanly
    scheduler.shutdown(wait=False)
    await redis_client.aclose()
    await engine.dispose()


app = FastAPI(title="WaitWatch API", version="0.1.0", lifespan=lifespan)

app.include_router(venues.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
