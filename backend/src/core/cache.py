"""Optional Redis caching layer. If REDIS_URL is not set, cache is a no-op."""
import json
from typing import Any, Optional

from src.core.config import get_settings

settings = get_settings()

_redis_client: Any = None
_CACHE_PREFIX = "crypto_analytics:"
_DEFAULT_TTL_SEC = 60


def _get_redis():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    if not settings.redis_url:
        return None
    try:
        import redis.asyncio as redis

        _redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        return _redis_client
    except Exception:
        return None


async def cache_get(key: str) -> Optional[str]:
    """Get value from cache. Returns None if cache is disabled or key missing."""
    client = _get_redis()
    if client is None:
        return None
    try:
        full_key = f"{_CACHE_PREFIX}{key}"
        return await client.get(full_key)
    except Exception:
        return None


async def cache_set(key: str, value: str, ttl_sec: int = _DEFAULT_TTL_SEC) -> None:
    """Set value in cache. No-op if cache is disabled."""
    client = _get_redis()
    if client is None:
        return
    try:
        full_key = f"{_CACHE_PREFIX}{key}"
        await client.setex(full_key, ttl_sec, value)
    except Exception:
        pass


async def cache_get_json(key: str) -> Optional[Any]:
    """Get JSON value from cache."""
    raw = await cache_get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


async def cache_set_json(key: str, value: Any, ttl_sec: int = _DEFAULT_TTL_SEC) -> None:
    """Set JSON value in cache."""
    raw = json.dumps(value, default=str)
    await cache_set(key, raw, ttl_sec)


async def cache_delete(key: str) -> None:
    """Delete key from cache."""
    client = _get_redis()
    if client is None:
        return
    try:
        await client.delete(f"{_CACHE_PREFIX}{key}")
    except Exception:
        pass
