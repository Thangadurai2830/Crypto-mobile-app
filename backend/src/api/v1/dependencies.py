"""
Dependency injection for API v1.

Centralizes get_db, get_settings, get_current_user, validated path/query params, and common query params (pagination, etc.).
"""
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, HTTPException, Path, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import decode_access_token, is_session_valid
from src.core.config import Settings, get_settings
from src.core.database import AsyncSessionLocal
from src.core.security import validate_symbol
from src.models.user import User

security_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session. Commits on success, rolls back on error."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_settings_dep() -> Settings:
    """Return application settings (e.g. for conditional logic in routes)."""
    return get_settings()


# Type aliases for use in route signatures
DbSession = Annotated[AsyncSession, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings_dep)]


def get_validated_symbol(
    symbol: str = Path(..., description="Asset symbol (e.g. BTC)"),
) -> str:
    """Validate and normalize symbol from path. Raises 422 if invalid."""
    try:
        return validate_symbol(symbol)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e


ValidatedSymbol = Annotated[str, Depends(get_validated_symbol)]


async def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)] = None,
) -> User:
    """Require valid JWT and return the user. Raises 401 if missing or invalid."""
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_id = int(payload["sub"])
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Validate session if JWT contains jti (session-based token)
    if payload.get("jti"):
        valid = await is_session_valid(db, payload["jti"])
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
    if user.account_status not in ("active", "pending_kyc"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active",
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


class PaginationParams:
    """Common pagination query params."""

    def __init__(
        self,
        limit: Annotated[int, Query(ge=1, le=500, description="Max items per page")] = 100,
        offset: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
    ):
        self.limit = limit
        self.offset = offset
