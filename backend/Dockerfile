FROM python:3.12-slim

# Prevents Python from writing .pyc files and buffers stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install deps in a separate layer so this step is cached unless requirements change
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source after deps so code changes don't invalidate the pip layer
COPY . .

EXPOSE 8000

# Production default: no --reload (docker-compose.yml adds it back for local dev).
# One process only: the stale-report scheduler runs inside it (DECISIONS #5), so
# extra workers would run the job several times.
# --proxy-headers: trust X-Forwarded-* from Caddy so logs show real client IPs.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
