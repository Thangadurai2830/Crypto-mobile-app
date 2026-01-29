# Backend Production Deployment

## Dockerfile (backend/docker/Dockerfile)

- **Base:** `python:3.11-slim`
- **System deps:** `gcc` (for building wheels), `postgresql-client` (optional: health/backup)
- **Python deps:** `requirements/base.txt` + `requirements/production.txt` (adds `gunicorn`)
- **App:** Copied into `/app` with `PYTHONPATH=/app`
- **CMD:** `gunicorn src.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000` with logs to stdout/stderr

## Build & run

```bash
# From repo root
docker compose build backend
docker compose up -d backend

# Or from backend/
docker build -f docker/Dockerfile -t crypto-backend .
docker run -p 8000:8000 -e DATABASE_URL=postgresql+asyncpg://... crypto-backend
```

## Environment

Set in docker-compose or at runtime:

- `DATABASE_URL` — PostgreSQL (recommended) or SQLite
- `REDIS_URL` — optional cache/rate limit
- `RATE_LIMIT_ENABLED`, `API_KEY_ENABLED`, `CORS_ORIGINS`, etc. (see `.env.example`)

## Single-worker (dev) override

To run uvicorn directly (no gunicorn) in docker-compose:

```yaml
backend:
  command: uvicorn src.main:app --host 0.0.0.0 --port 8000
```
