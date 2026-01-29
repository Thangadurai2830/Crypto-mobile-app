# Dockerfile.backend — Production deployment
FROM python:3.11-slim

# Install system dependencies (gcc for some wheels; postgresql-client for pg_isready/backup)
RUN apt-get update && apt-get install -y \
  gcc \
  postgresql-client \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies (production = base + gunicorn)
COPY requirements/base.txt requirements/
COPY requirements/production.txt requirements/
RUN pip install --no-cache-dir -r requirements/production.txt

# Copy application
COPY . .

# Ensure app is importable
ENV PYTHONPATH=/app

# Default env (override in docker-compose or at runtime)
ENV DATABASE_URL=sqlite+aiosqlite:///./crypto_analytics.db

EXPOSE 8000

# Production: gunicorn with uvicorn workers
CMD [
"gunicorn",
"src.main:app",
"--workers", "4",
"--worker-class", "uvicorn.workers.UvicornWorker",
"--bind", "0.0.0.0:8000",
"--access-logfile", "-",
"--error-logfile", "-",
"--capture-output"
]
