"""Application configuration."""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_name: str = "Crypto Market Analytics API"
    debug: bool = False

    # Database - PostgreSQL (production) or SQLite (dev)
    database_url: str = "sqlite+aiosqlite:///./crypto_analytics.db"

    # Data source
    data_source: Literal["coingecko", "binance", "both"] = "coingecko"
    coingecko_base_url: str = "https://api.coingecko.com/api/v3"
    binance_base_url: str = "https://api.binance.com"

    # Ingestion
    top_n_assets: int = 10
    fetch_interval_minutes: int = 5
    # Scheduled jobs
    analytics_interval_minutes: int = 15
    strategy_interval_minutes: int = 60
    cleanup_interval_hours: int = 24
    market_data_retention_days: int = 30
    analytics_results_retention_days: int = 7
    strategy_runs_retention_days: int = 30
    # CoinGecko client
    coingecko_request_timeout_sec: float = 30.0
    coingecko_max_retries: int = 3
    coingecko_retry_backoff_sec: float = 2.0
    coingecko_rate_limit_calls_per_minute: int = 10

    # Analytics
    default_price_window_hours: int = 24
    default_volume_window_hours: int = 24

    # Strategy
    ma_fast_period: int = 7
    ma_slow_period: int = 21
    ma_short_period: int = 10
    ma_long_period: int = 30
    momentum_threshold_pct: float = 5.0
    rsi_period: int = 14
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0
    volume_confirmation_ratio: float = 1.0

    # CORS (Flutter web uses a random port, e.g. 60996; allow any localhost port when True)
    cors_allow_localhost_any_port: bool = True  # Allow http://localhost:* and http://127.0.0.1:* for Flutter web
    # Regex for any localhost port (Flutter web, Vite, etc.). Used by CORSMiddleware when cors_allow_localhost_any_port is True.
    cors_localhost_regex: str = r"^http://localhost(:\d+)?$|^http://127\.0\.0\.1(:\d+)?$"
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
    ]
    cors_expose_headers: list[str] = ["X-Request-ID", "X-Response-Time-Ms", "X-RateLimit-Limit", "X-RateLimit-Remaining"]
    cors_max_age: int = 600  # seconds

    # Rate limiting (per client IP)
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60
    rate_limit_window_seconds: int = 60

    # API key (optional: leave empty to disable; set both for rotation window)
    api_key_enabled: bool = False
    api_key_current: str = ""
    api_key_previous: str = ""  # accepted during rotation window

    # Auth (JWT, tokens)
    jwt_secret: str = "change-me-in-production-use-long-random-string"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15  # 15 min expiry
    refresh_token_expire_days: int = 7  # 7 days expiry; rotation on refresh
    email_verification_expire_hours: int = 24
    password_reset_expire_minutes: int = 60
    frontend_url: str = "http://localhost:3000"  # For email links (verify, reset)
    # Auth rate limiting: login/register attempts per identifier (email or IP)
    auth_rate_limit_attempts_per_hour: int = 5
    auth_rate_limit_window_seconds: int = 3600  # 1 hour
    # Password policy
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_digit: bool = True
    password_require_special: bool = True
    # 2FA temp token (for completing login after password)
    two_fa_temp_token_expire_minutes: int = 5
    # Session management
    session_expire_days: int = 30

    # Redis (optional: leave empty to disable caching)
    redis_url: str = ""

    # DB pool (for async engines that support it)
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # Observability
    log_level: str = "INFO"
    log_json: bool = True
    sentry_dsn: str = ""
    sentry_environment: str = ""
    sentry_traces_sample_rate: float = 0.1


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
