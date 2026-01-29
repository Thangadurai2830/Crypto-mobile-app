"""
Security utilities: API key auth (with rotation), input validation.

- API key: optional; supports current + previous key for rotation.
- Input validation: symbol format, strategy name allowlist (no raw SQL with user input).

JWT (see src.core.auth): Access tokens 15 min expiry; refresh tokens 7 days; token blacklisting
on logout; token rotation on refresh (old refresh token revoked).
"""
import re
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from src.core.config import get_settings

settings = get_settings()

# For OpenAPI/Swagger: shows "Authorize" and X-API-Key header in interactive docs
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False, description="API key (required when API_KEY_ENABLED=true). Supports rotation: current or previous key.")

# Symbol: alphanumeric, 1–20 chars (e.g. BTC, ETH, wrapped-BTC)
SYMBOL_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\-.]{0,19}$")

# Allowed strategy names (must match StrategyFactory in strategy.py)
ALLOWED_STRATEGY_NAMES = frozenset({
    "ma_crossover",
    "momentum",
    "momentum_rsi",
})


def validate_symbol(value: str) -> str:
    """
    Validate and normalize symbol. Raises ValueError if invalid.
    Returns uppercase symbol for consistency.
    """
    if not value or len(value) > 20:
        raise ValueError("Symbol must be 1–20 characters")
    cleaned = value.strip().upper()
    if not cleaned or len(cleaned) > 20:
        raise ValueError("Symbol must be 1–20 characters")
    if not SYMBOL_PATTERN.match(cleaned):
        raise ValueError("Symbol must be alphanumeric (allowed: letters, numbers, hyphen, dot)")
    return cleaned


def validate_strategy_name(value: str) -> str:
    """Validate strategy name against allowlist. Raises ValueError if invalid."""
    if value not in ALLOWED_STRATEGY_NAMES:
        raise ValueError(f"Strategy must be one of: {sorted(ALLOWED_STRATEGY_NAMES)}")
    return value


async def require_api_key(
    api_key: Optional[str] = Depends(API_KEY_HEADER),
) -> Optional[str]:
    """
    Dependency: when API key is enabled, require X-API-Key header to match current or previous key.
    Returns the key value if auth is disabled or key is valid.
    """
    if not settings.api_key_enabled:
        return api_key
    if not api_key or not api_key.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    key = api_key.strip()
    if settings.api_key_current and key == settings.api_key_current:
        return key
    if settings.api_key_previous and key == settings.api_key_previous:
        return key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "ApiKey"},
    )
