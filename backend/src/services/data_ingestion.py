"""
Data Ingestion Service:

1. CoinGecko API client with retry logic (exponential backoff)
2. Rate limiting implementation (calls per minute)
3. Data validation and transformation (Pydantic)
4. Bulk insert optimization (batch flush)
5. Error handling and logging
"""
import asyncio
import logging
import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import httpx
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.models.market import CryptoAsset, MarketData

logger = logging.getLogger(__name__)
settings = get_settings()


# ----- Rate limiter -----
class RateLimiter:
    """Simple rate limiter: max N calls per minute."""

    def __init__(self, calls_per_minute: int) -> None:
        self._calls_per_minute = max(1, calls_per_minute)
        self._timestamps: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            cutoff = now - 60.0
            self._timestamps = [t for t in self._timestamps if t > cutoff]
            if len(self._timestamps) >= self._calls_per_minute:
                sleep_until = self._timestamps[0] + 60.0 - now
                if sleep_until > 0:
                    logger.debug("Rate limit: sleeping %.1fs", sleep_until)
                    await asyncio.sleep(sleep_until)
                now = time.monotonic()
                self._timestamps = [t for t in self._timestamps if t > now - 60.0]
            self._timestamps.append(time.monotonic())


# ----- Data validation and transformation -----
class CoinGeckoMarketRow(BaseModel):
    """Validated row from CoinGecko /coins/markets response."""

    id: str = Field(..., description="CoinGecko coin id")
    symbol: str = Field(..., min_length=1, max_length=20)
    name: str | None = Field(None, max_length=255)
    current_price: Decimal = Field(..., ge=0)
    total_volume: Decimal | None = Field(None, ge=0)

    @field_validator("symbol", mode="before")
    @classmethod
    def symbol_upper(cls, v: Any) -> str:
        if isinstance(v, str):
            return v.upper()[:20]
        return str(v).upper()[:20]

    @field_validator("current_price", mode="before")
    @classmethod
    def current_price_decimal(cls, v: Any) -> Decimal:
        if v is None:
            return Decimal("0")
        try:
            return Decimal(str(v))
        except Exception:
            return Decimal("0")

    @field_validator("total_volume", mode="before")
    @classmethod
    def total_volume_decimal(cls, v: Any) -> Decimal | None:
        if v is None:
            return None
        try:
            return Decimal(str(v))
        except Exception:
            return None


def _symbol_from_coingecko_id(coin_id: str) -> str:
    """Map CoinGecko id to common symbol."""
    mapping = {
        "bitcoin": "BTC",
        "ethereum": "ETH",
        "tether": "USDT",
        "binancecoin": "BNB",
        "solana": "SOL",
        "ripple": "XRP",
        "usd-coin": "USDC",
        "cardano": "ADA",
        "avalanche-2": "AVAX",
        "dogecoin": "DOGE",
        "polkadot": "DOT",
        "chainlink": "LINK",
        "tron": "TRX",
        "polygon": "MATIC",
        "shiba-inu": "SHIB",
        "litecoin": "LTC",
        "uniswap": "UNI",
    }
    return mapping.get(coin_id.lower(), coin_id.upper()[:6])


def validate_and_transform_markets(raw: list[dict[str, Any]]) -> list[CoinGeckoMarketRow]:
    """Validate and transform raw API response into typed rows. Skips invalid rows."""
    out: list[CoinGeckoMarketRow] = []
    for i, row in enumerate(raw):
        try:
            symbol = _symbol_from_coingecko_id(row.get("id") or "")
            parsed = CoinGeckoMarketRow(
                id=row.get("id") or "",
                symbol=symbol,
                name=row.get("name"),
                current_price=row.get("current_price") or 0,
                total_volume=row.get("total_volume"),
            )
            out.append(parsed)
        except Exception as e:
            logger.warning("Skip invalid market row at index %s: %s", i, e)
    return out


# ----- Circuit breaker for external API -----
class CircuitBreaker:
    """Simple circuit breaker: open after N consecutive failures; cooldown before retry."""

    def __init__(self, failure_threshold: int = 5, cooldown_sec: float = 60.0) -> None:
        self._failure_threshold = max(1, failure_threshold)
        self._cooldown_sec = max(1.0, cooldown_sec)
        self._failures = 0
        self._last_failure_time: float = 0.0
        self._lock = asyncio.Lock()

    async def call(self, coro):  # type: ignore
        """Execute coroutine; on exception increment failures; when open raise without calling."""
        async with self._lock:
            now = time.monotonic()
            if self._failures >= self._failure_threshold:
                if now - self._last_failure_time < self._cooldown_sec:
                    raise RuntimeError(
                        f"Circuit breaker open (cooldown {self._cooldown_sec}s); skipping external API call"
                    )
                self._failures = 0
        try:
            result = await coro
            async with self._lock:
                self._failures = 0
            return result
        except Exception:
            async with self._lock:
                self._failures += 1
                self._last_failure_time = time.monotonic()
            raise


_coingecko_circuit: CircuitBreaker | None = None


def _get_coingecko_circuit() -> CircuitBreaker:
    global _coingecko_circuit
    if _coingecko_circuit is None:
        _coingecko_circuit = CircuitBreaker(failure_threshold=5, cooldown_sec=60.0)
    return _coingecko_circuit


# ----- CoinGecko API client with retry and rate limiting -----
_rate_limiter: RateLimiter | None = None


def _get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(settings.coingecko_rate_limit_calls_per_minute)
    return _rate_limiter


async def _fetch_with_retry(
    client: httpx.AsyncClient,
    url: str,
    params: dict[str, Any],
    retries_left: int | None = None,
) -> list[dict[str, Any]]:
    """GET request with exponential backoff retry. Returns JSON list."""
    retries_left = retries_left if retries_left is not None else settings.coingecko_max_retries
    backoff = settings.coingecko_retry_backoff_sec
    last_exc: Exception | None = None
    for attempt in range(retries_left + 1):
        try:
            resp = await client.get(url, params=params)
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", backoff * (2**attempt)))
                logger.warning("Rate limited (429); retry after %ss", retry_after)
                await asyncio.sleep(min(retry_after, 60))
                continue
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            last_exc = e
            if e.response.status_code >= 500 and attempt < retries_left:
                wait = backoff * (2**attempt)
                logger.warning("Server error %s; retry in %.1fs", e.response.status_code, wait)
                await asyncio.sleep(wait)
            else:
                raise
        except (httpx.RequestError, asyncio.TimeoutError) as e:
            last_exc = e
            if attempt < retries_left:
                wait = backoff * (2**attempt)
                logger.warning("Request failed: %s; retry in %.1fs", e, wait)
                await asyncio.sleep(wait)
            else:
                raise
    if last_exc:
        raise last_exc
    return []


async def fetch_coingecko_markets(per_page: int = 10) -> list[dict[str, Any]]:
    """Fetch top N coins from CoinGecko markets endpoint. Raw JSON (no validation). Circuit breaker + rate limit + retry."""
    async def _fetch() -> list[dict[str, Any]]:
        limiter = _get_rate_limiter()
        await limiter.acquire()
        url = f"{settings.coingecko_base_url}/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": per_page,
            "page": 1,
            "sparkline": "false",
        }
        async with httpx.AsyncClient(timeout=settings.coingecko_request_timeout_sec) as client:
            data = await _fetch_with_retry(client, url, params)
        return data if isinstance(data, list) else []

    try:
        return await _get_coingecko_circuit().call(_fetch())
    except RuntimeError as e:
        logger.warning("Circuit breaker open: %s", e)
        return []


async def fetch_coingecko_market_chart(coin_id: str, days: int = 1) -> dict[str, Any]:
    """Fetch market chart (prices, volumes) for a coin. Circuit breaker + rate limit + retry."""
    async def _fetch() -> dict[str, Any]:
        limiter = _get_rate_limiter()
        await limiter.acquire()
        url = f"{settings.coingecko_base_url}/coins/{coin_id}/market_chart"
        params = {"vs_currency": "usd", "days": days}
        async with httpx.AsyncClient(timeout=settings.coingecko_request_timeout_sec) as client:
            data = await _fetch_with_retry(client, url, params)
        return data if isinstance(data, dict) else {}

    try:
        return await _get_coingecko_circuit().call(_fetch())
    except RuntimeError as e:
        logger.warning("Circuit breaker open: %s", e)
        return {}


# ----- Bulk insert and orchestration -----
async def ensure_assets(session: AsyncSession, top_n: int) -> list[CryptoAsset]:
    """Ensure crypto assets exist for top N coins; create if missing. Caller commits."""
    raw = await fetch_coingecko_markets(per_page=top_n)
    rows = validate_and_transform_markets(raw)
    if not rows:
        logger.warning("No valid market rows from CoinGecko")
        return []
    existing = await session.execute(
        select(CryptoAsset).where(
            CryptoAsset.symbol.in_([_symbol_from_coingecko_id(r.id) for r in rows])
        )
    )
    by_symbol = {a.symbol: a for a in existing.scalars().all()}
    assets: list[CryptoAsset] = []
    for r in rows:
        symbol = _symbol_from_coingecko_id(r.id)
        if symbol not in by_symbol:
            asset = CryptoAsset(symbol=symbol, name=r.name, coingecko_id=r.id)
            session.add(asset)
            await session.flush()
            by_symbol[symbol] = asset
        assets.append(by_symbol[symbol])
    return assets


async def ingest_latest_prices(session: AsyncSession, top_n: int | None = None) -> int:
    """
    Ingest latest price/volume for top N assets.
    Uses CoinGecko markets with retry, rate limit, validation, and bulk insert.
    Caller is responsible for commit.
    Returns count of records inserted.
    """
    n = top_n or settings.top_n_assets
    logger.info("Ingestion started: top_n=%s", n)
    try:
        raw = await fetch_coingecko_markets(per_page=n)
    except Exception as e:
        logger.exception("CoinGecko fetch failed: %s", e)
        raise
    rows = validate_and_transform_markets(raw)
    if not rows:
        logger.warning("No valid rows after validation")
        return 0
    now = datetime.now(timezone.utc)
    # Resolve symbol -> asset (get or create) in one pass
    symbols = [_symbol_from_coingecko_id(r.id) for r in rows]
    existing = await session.execute(select(CryptoAsset).where(CryptoAsset.symbol.in_(symbols)))
    by_symbol = {a.symbol: a for a in existing.scalars().all()}
    to_create: list[tuple[str, str | None, str]] = []
    for r in rows:
        sym = _symbol_from_coingecko_id(r.id)
        if sym not in by_symbol:
            to_create.append((sym, r.name, r.id))
    created: list[tuple[str, CryptoAsset]] = []
    for symbol, name, coingecko_id in to_create:
        asset = CryptoAsset(symbol=symbol, name=name, coingecko_id=coingecko_id)
        session.add(asset)
        created.append((symbol, asset))
    if created:
        await session.flush()
        for symbol, asset in created:
            by_symbol[symbol] = asset
    # Bulk build MarketData rows
    market_records: list[MarketData] = []
    for r in rows:
        sym = _symbol_from_coingecko_id(r.id)
        asset = by_symbol.get(sym)
        if not asset:
            continue
        market_records.append(
            MarketData(
                asset_id=asset.id,
                symbol=asset.symbol,
                price=r.current_price,
                volume=r.total_volume,
                timestamp=now,
            )
        )
    for rec in market_records:
        session.add(rec)
    if market_records:
        await session.flush()
    count = len(market_records)
    logger.info("Ingestion finished: inserted=%s", count)
    return count
