"""Detailed health checks for database and Redis."""
from sqlalchemy import text

from src.core.cache import _get_redis
from src.core.config import get_settings
from src.core.database import AsyncSessionLocal

settings = get_settings()


async def check_database() -> dict:
    """Check database connectivity. Returns { status: 'ok' | 'error', message?: str }."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def check_redis() -> dict:
    """Check Redis connectivity if configured. Returns { status: 'ok' | 'error' | 'skipped', message?: str }."""
    if not settings.redis_url:
        return {"status": "skipped", "message": "Redis not configured"}
    client = _get_redis()
    if client is None:
        return {"status": "error", "message": "Redis client not initialized"}
    try:
        await client.ping()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
