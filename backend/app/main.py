from fastapi import FastAPI

from app.routes import venues

app = FastAPI(title="WaitWatch API", version="0.1.0")

app.include_router(venues.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
