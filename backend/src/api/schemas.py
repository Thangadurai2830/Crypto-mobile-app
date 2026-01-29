"""Pydantic request/response schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from src.core.security import validate_strategy_name


# ----- Auth -----
def _validate_password_complexity(v: str) -> str:
    """Used by RegisterRequest and ResetPasswordRequest; backend also enforces in core.auth."""
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not __import__("re").search(r"[A-Z]", v):
        raise ValueError("Password must contain at least one uppercase letter")
    if not __import__("re").search(r"[a-z]", v):
        raise ValueError("Password must contain at least one lowercase letter")
    if not __import__("re").search(r"\d", v):
        raise ValueError("Password must contain at least one digit")
    if not __import__("re").search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", v):
        raise ValueError("Password must contain at least one special character")
    return v


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: Optional[str] = Field(None, max_length=100)

    @field_validator("password")
    @classmethod
    def password_policy(cls, v: str) -> str:
        return _validate_password_complexity(v)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    refresh_token: Optional[str] = None  # 7 days; rotation on refresh
    refresh_expires_in: Optional[int] = None  # seconds


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class Login2FAResponse(BaseModel):
    """Returned when user has 2FA enabled; client must call POST /auth/2fa/complete-login with temp_token + code."""
    requires_2fa: bool = True
    temp_token: str
    expires_in: int  # seconds


class VerifyEmailRequest(BaseModel):
    token: str = Field(..., min_length=1)


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class RequestPasswordResetRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_policy(cls, v: str) -> str:
        return _validate_password_complexity(v)


class KYCLevel1Request(BaseModel):
    """KYC Level 1: phone (required) and optional name fields."""
    phone: str = Field(..., min_length=8, max_length=32)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)


class TwoFACompleteLoginRequest(BaseModel):
    """Complete login after password when 2FA is enabled."""
    temp_token: str = Field(..., min_length=1)
    code: str = Field(..., min_length=6, max_length=6)


class TwoFactorEnableResponse(BaseModel):
    secret: str  # Base32 for TOTP app
    qr_code_uri: str


class TwoFactorVerifyRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)


class UserProfileResponse(BaseModel):
    display_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    kyc_level: str
    timezone: Optional[str] = None
    locale: Optional[str] = None

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: int
    email: str
    account_status: str
    is_email_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
    profile: Optional[UserProfileResponse] = None

    model_config = {"from_attributes": True}


# ----- Market -----
class PriceRecordSchema(BaseModel):
    symbol: str
    price: Decimal
    volume: Optional[Decimal] = None
    timestamp: datetime

    model_config = {"from_attributes": True}


class MarketAssetSchema(BaseModel):
    id: int
    symbol: str
    name: Optional[str] = None
    coingecko_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MarketAssetWithLatestPrice(MarketAssetSchema):
    latest_price: Optional[Decimal] = None
    latest_volume: Optional[Decimal] = None
    latest_timestamp: Optional[datetime] = None


# ----- Analytics -----
class MacdSchema(BaseModel):
    macd_line: float
    signal_line: float
    histogram: float


class AssetAnalyticsSchema(BaseModel):
    symbol: str
    price_change_pct: Optional[float] = None
    volume_change_pct: Optional[float] = None
    momentum: Optional[float] = None
    current_price: Optional[Decimal] = None
    current_volume: Optional[Decimal] = None
    window_hours: int = 24
    sma_20: Optional[float] = None
    ema_20: Optional[float] = None
    volume_ratio_20: Optional[float] = None
    rsi_14: Optional[float] = None
    macd: Optional[MacdSchema] = None
    rank: Optional[int] = None


class AnalyticsResponse(BaseModel):
    window_hours: int
    computed_at: datetime
    assets: list[AssetAnalyticsSchema]


# ----- Strategy -----
class StrategySignalSchema(BaseModel):
    symbol: str
    signal: str  # BUY, SELL, HOLD
    price_at_signal: Optional[str] = None
    reason: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class StrategyRunSchema(BaseModel):
    id: int
    run_at: datetime
    strategy_name: str
    params_snapshot: Optional[str] = None
    status: str
    signals: list[StrategySignalSchema] = []

    model_config = {"from_attributes": True}


class StrategyRunRequest(BaseModel):
    """Request body for POST /v1/strategy/run."""

    strategy_name: str = Field(
        default="ma_crossover",
        description="Strategy to run: ma_crossover, momentum, momentum_rsi",
    )
    limit_per_symbol: int = Field(
        default=100,
        ge=10,
        le=500,
        description="History points per symbol for backtest",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"strategy_name": "ma_crossover", "limit_per_symbol": 100},
                {"strategy_name": "momentum_rsi", "limit_per_symbol": 200},
            ]
        }
    }

    @field_validator("strategy_name")
    @classmethod
    def strategy_name_allowed(cls, v: str) -> str:
        try:
            return validate_strategy_name(v)
        except ValueError as e:
            raise ValueError(str(e)) from e
