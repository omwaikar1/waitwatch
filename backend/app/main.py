from fastapi import FastAPI

# WaitWatch API — Session 2 started
app = FastAPI(title="WaitWatch API", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "ok"}
