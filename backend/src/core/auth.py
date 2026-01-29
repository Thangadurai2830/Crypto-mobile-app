"""Auth utilities: password hashing, JWT creation/verification, token generation."""
import re
import uuid
from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import insert, select, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.models.user import Session

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def validate_password_policy(plain: str) -> None:
    """Validate password against policy. Raises ValueError with message if invalid."""
    min_len = getattr(settings, "password_min_length", 8)
    if len(plain) < min_len:
        raise ValueError(f"Password must be at least {min_len} characters")
    if getattr(settings, "password_require_uppercase", True) and not re.search(r"[A-Z]", plain):
        raise ValueError("Password must contain at least one uppercase letter")
    if getattr(settings, "password_require_lowercase", True) and not re.search(r"[a-z]", plain):
        raise ValueError("Password must contain at least one lowercase letter")
    if getattr(settings, "password_require_digit", True) and not re.search(r"\d", plain):
        raise ValueError("Password must contain at least one digit")
    if getattr(settings, "password_require_special", True) and not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", plain):
        raise ValueError("Password must contain at least one special character")


def hash_password(plain: str) -> str:
    """Hash a plain password for storage."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against a hash."""
    return pwd_context.verify(plain, hashed)


def create_access_token(
    subject: str | int,
    extra_claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token. subject is typically user id."""
    to_encode = {"sub": str(subject), "type": "access"}
    if extra_claims:
        to_encode.update(extra_claims)
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode["exp"] = expire
    to_encode["iat"] = datetime.now(timezone.utc)
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_temp_2fa_token(user_id: int) -> str:
    """Create a short-lived JWT for completing 2FA login. Payload: sub=user_id, type=2fa_temp."""
    expire_min = getattr(settings, "two_fa_temp_token_expire_minutes", 5)
    expires_delta = timedelta(minutes=expire_min)
    return create_access_token(
        subject=user_id,
        extra_claims={"type": "2fa_temp"},
        expires_delta=expires_delta,
    )


def decode_temp_2fa_token(token: str) -> int | None:
    """Decode 2FA temp token; return user_id or None."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != "2fa_temp" or "sub" not in payload:
            return None
        return int(payload["sub"])
    except (JWTError, ValueError, TypeError):
        return None


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and validate JWT; return payload or None if invalid."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def create_refresh_token(
    subject: str | int,
    refresh_jti: str,
    sid: int,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT refresh token (7 days). Rotation: old token blacklisted on refresh."""
    expire_days = getattr(settings, "refresh_token_expire_days", 7)
    delta = expires_delta or timedelta(days=expire_days)
    expire = datetime.now(timezone.utc) + delta
    to_encode = {
        "sub": str(subject),
        "type": "refresh",
        "refresh_jti": refresh_jti,
        "sid": sid,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_refresh_token(token: str) -> dict[str, Any] | None:
    """Decode and validate refresh JWT; return payload or None if invalid."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != "refresh" or "refresh_jti" not in payload or "sub" not in payload:
            return None
        return payload
    except JWTError:
        return None


async def create_session(
    db: AsyncSession,
    user_id: int,
    ip_address: str | None = None,
    user_agent: str | None = None,
    device_fingerprint: str | None = None,
) -> tuple[str, str | None, int]:
    """Create a session row and return (jti, refresh_jti, session_id). refresh_jti is None if DB has no refresh_jti column (run migration 005)."""
    jti = str(uuid.uuid4())
    refresh_jti = str(uuid.uuid4())
    expire_days = getattr(settings, "refresh_token_expire_days", 7)
    expires_at = datetime.now(timezone.utc) + timedelta(days=expire_days)
    session = Session(
        user_id=user_id,
        jti=jti,
        refresh_jti=refresh_jti,
        device_fingerprint=device_fingerprint,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=expires_at,
    )
    try:
        db.add(session)
        await db.flush()
        return jti, refresh_jti, session.id
    except OperationalError:
        await db.rollback()
        result = await db.execute(
            insert(Session.__table__).values(
                user_id=user_id,
                jti=jti,
                device_fingerprint=device_fingerprint,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=expires_at,
            ).returning(Session.__table__.c.id)
        )
        row = result.one()
        await db.flush()
        return jti, None, row[0]


async def invalidate_session_by_jti(db: AsyncSession, jti: str) -> bool:
    """Revoke session by access JWT id (blacklist). Returns True if a session was revoked."""
    result = await db.execute(update(Session).where(Session.jti == jti).values(revoked_at=datetime.now(timezone.utc)))
    return result.rowcount > 0


async def invalidate_session_by_refresh_jti(db: AsyncSession, refresh_jti: str) -> bool:
    """Revoke session by refresh JWT id (token rotation blacklist). Returns True if revoked."""
    result = await db.execute(
        update(Session).where(Session.refresh_jti == refresh_jti).values(revoked_at=datetime.now(timezone.utc))
    )
    return result.rowcount > 0


async def is_session_valid(db: AsyncSession, jti: str) -> bool:
    """Check if session exists, not expired, and not revoked."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Session).where(
            Session.jti == jti,
            Session.expires_at > now,
            Session.revoked_at.is_(None),
        )
    )
    return result.scalar_one_or_none() is not None


async def is_refresh_session_valid(db: AsyncSession, refresh_jti: str) -> bool:
    """Check if session exists for this refresh_jti, not expired, and not revoked."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Session).where(
            Session.refresh_jti == refresh_jti,
            Session.expires_at > now,
            Session.revoked_at.is_(None),
        )
    )
    return result.scalar_one_or_none() is not None


def generate_email_verification_token() -> str:
    """Generate a secure token for email verification."""
    return token_urlsafe(32)


def generate_password_reset_token() -> str:
    """Generate a secure token for password reset."""
    return token_urlsafe(32)
