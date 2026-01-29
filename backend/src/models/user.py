"""
User Models Structure:
1. User - Base user information (email, password hash, account status)
2. UserProfile - Additional user details (name, KYC level, etc.)
3. LoginHistory - Audit trail for logins
4. SecuritySettings - 2FA, API keys, password reset tokens

Features: email verification, password reset, 2FA, KYC levels, account status.
"""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class AccountStatus(str, PyEnum):
    """Account lifecycle status."""

    PENDING_VERIFICATION = "pending_verification"  # Registered, email not verified
    PENDING_KYC = "pending_kyc"  # Email verified, KYC Level 1 not yet completed
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


class KycLevel(str, PyEnum):
    """KYC verification level."""

    NONE = "none"
    BASIC = "basic"  # Email + phone
    STANDARD = "standard"  # ID document
    ENHANCED = "enhanced"  # Full due diligence


class User(Base):
    """
    Base user: credentials and account status.
    Email is unique; password stored as hash.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    account_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=AccountStatus.PENDING_VERIFICATION.value,
    )
    is_email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    login_history: Mapped[list["LoginHistory"]] = relationship(
        "LoginHistory",
        back_populates="user",
        order_by="LoginHistory.login_at.desc()",
        cascade="all, delete-orphan",
    )
    security_settings: Mapped[Optional["SecuritySettings"]] = relationship(
        "SecuritySettings",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    sessions: Mapped[list["Session"]] = relationship(
        "Session",
        back_populates="user",
        order_by="Session.created_at.desc()",
        cascade="all, delete-orphan",
    )


class UserProfile(Base):
    """Extended user details: display name, KYC, phone, etc."""

    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    kyc_level: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=KycLevel.NONE.value,
    )
    kyc_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    locale: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship("User", back_populates="profile")


class LoginHistory(Base):
    """Audit trail: each login attempt (success or failure)."""

    __tablename__ = "login_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    login_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    device_fingerprint: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="login_history")


class SecuritySettings(Base):
    """2FA, API keys, password reset tokens, email verification tokens."""

    __tablename__ = "security_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    two_factor_secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # TOTP secret (encrypted in prod)
    email_verification_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email_verification_token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    password_reset_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    password_reset_token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    api_key_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Optional per-user API key
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship("User", back_populates="security_settings")


class Session(Base):
    """User session: JWT id (jti) + device fingerprint for logout / invalidation."""

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    jti: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)  # JWT ID for access token
    refresh_jti: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True, index=True)  # JWT ID for refresh token (rotation)
    device_fingerprint: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="sessions")
