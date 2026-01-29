"""
Rate limiting: in-memory or Redis-backed, per client identifier (e.g. IP).

Used by RateLimitMiddleware to enforce configurable request limits per window.
"""
import time
from collections import defaultdict
from typing import Optional

from src.core.config import get_settings

settings = get_settings()

# In-memory: key -> list of timestamps (request times in the current window)
_memory_store: dict[str, list[float]] = defaultdict(list)
_MEMORY_CLEANUP_AFTER = 1000  # trim when we have this many keys


def _memory_key(identifier: str) -> str:
    return f"rl:{identifier}"


_redis_client = None


def _get_redis_client():
    """Lazy Redis client for rate limit counters (cached)."""
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


async def _redis_increment_and_get(key: str, window_sec: int) -> tuple[int, int]:
    """
    Increment counter in Redis with sliding window (key expires after window_sec).
    Returns (current_count, ttl_seconds).
    """
    client = _get_redis_client()
    if client is None:
        return 0, 0
    try:
        pipe = client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_sec)
        pipe.ttl(key)
        results = await pipe.execute()
        count = int(results[0]) if results[0] else 0
        ttl = int(results[2]) if len(results) > 2 and results[2] is not None else window_sec
        return count, max(0, ttl)
    except Exception:
        return 0, 0


def _memory_increment_and_get(identifier: str, window_sec: int) -> tuple[int, int]:
    """
    In-memory sliding window: drop timestamps outside window, then add current time.
    Returns (current_count, seconds_until_oldest_expires).
    """
    now = time.monotonic()
    key = _memory_key(identifier)
    lst = _memory_store[key]
    cutoff = now - window_sec
    while lst and lst[0] < cutoff:
        lst.pop(0)
    lst.append(now)
    # TTL: until the oldest entry in the list expires
    ttl = int(window_sec - (now - lst[0])) if lst else 0
    return len(lst), max(0, ttl)


async def check_rate_limit(identifier: str) -> tuple[bool, int, int]:
    """
    Check and consume one request for the given identifier.
    Returns (allowed, limit, remaining).
    limit = max requests per window; remaining = max(0, limit - current_count).
    """
    limit = settings.rate_limit_requests_per_minute
    window_sec = settings.rate_limit_window_seconds
    if not settings.rate_limit_enabled or limit <= 0:
        return True, limit, limit

    if settings.redis_url:
        key = f"crypto_analytics:ratelimit:{identifier}"
        count, _ = await _redis_increment_and_get(key, window_sec)
    else:
        count, _ = _memory_increment_and_get(identifier, window_sec)

    allowed = count <= limit
    remaining = max(0, limit - count)
    return allowed, limit, remaining


def _auth_memory_increment_and_get(identifier: str, window_sec: int) -> tuple[int, int]:
    """Auth-specific in-memory window: 5 attempts per hour per identifier."""
    key = f"auth_rl:{identifier}"
    now = time.monotonic()
    cutoff = now - window_sec
    if key not in _memory_store:
        _memory_store[key] = []
    lst = _memory_store[key]
    while lst and lst[0] < cutoff:
        lst.pop(0)
    lst.append(now)
    ttl = int(window_sec - (now - lst[0])) if lst else 0
    return len(lst), max(0, ttl)


async def check_auth_rate_limit(identifier: str) -> tuple[bool, int]:
    """
    Check and consume one auth attempt (login/register) for the given identifier.
    Uses auth_rate_limit_attempts_per_hour (default 5) per auth_rate_limit_window_seconds (1 hour).
    Returns (allowed, remaining_attempts).
    """
    limit = getattr(settings, "auth_rate_limit_attempts_per_hour", 5)
    window_sec = getattr(settings, "auth_rate_limit_window_seconds", 3600)
    if limit <= 0:
        return True, limit
    count, _ = _auth_memory_increment_and_get(identifier, window_sec)
    allowed = count <= limit
    remaining = max(0, limit - count)
    return allowed, remaining
