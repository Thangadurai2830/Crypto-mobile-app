"""
Analytics Computation:

1. Percentage change calculations (price, volume)
2. Moving averages (SMA, EMA)
3. Volume analysis (change %, ratio to average)
4. Momentum indicators (RSI, MACD)
5. Performance ranking algorithms
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.analytics import AnalyticsResult
from src.models.market import MarketData


# ----- Data loading -----
async def get_price_history(
    session: AsyncSession,
    symbol: str,
    limit: int = 500,
    since: Optional[datetime] = None,
) -> pd.DataFrame:
    """Load price history for one symbol into a DataFrame."""
    q = (
        select(MarketData.timestamp, MarketData.price, MarketData.volume)
        .where(MarketData.symbol == symbol)
        .order_by(MarketData.timestamp.desc())
        .limit(limit)
    )
    if since is not None:
        q = q.where(MarketData.timestamp >= since)
    result = await session.execute(q)
    rows = result.all()
    if not rows:
        return pd.DataFrame(columns=["timestamp", "price", "volume"])
    df = pd.DataFrame(rows, columns=["timestamp", "price", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.sort_values("timestamp").reset_index(drop=True)
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0)
    return df


async def get_all_symbols(session: AsyncSession) -> list[str]:
    """List distinct symbols that have price records."""
    q = select(MarketData.symbol).distinct()
    result = await session.execute(q)
    return [r[0] for r in result.all()]


# ----- 1. Percentage change calculations -----
def compute_pct_change(series: pd.Series, window: int) -> Optional[float]:
    """Generic percentage change: (current - past) / past * 100 over last `window` points."""
    if len(series) < window + 1:
        return None
    old = series.iloc[-1 - window]
    new = series.iloc[-1]
    if old == 0 or pd.isna(old):
        return None
    return float((new - old) / old * 100)


def compute_price_change_pct(series: pd.Series, window: int) -> Optional[float]:
    """Price change % over last `window` points."""
    return compute_pct_change(series, window)


def compute_volume_change_pct(series: pd.Series, window: int) -> Optional[float]:
    """Volume change % over last `window` points."""
    if len(series) < window + 1:
        return None
    old = series.iloc[-1 - window]
    new = series.iloc[-1]
    if old == 0 or pd.isna(old):
        return 0.0 if (new == 0 or pd.isna(new)) else None
    return float((new - old) / old * 100)


# ----- 2. Moving averages (SMA, EMA) -----
def sma(series: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average."""
    return series.rolling(window=period, min_periods=1).mean()


def ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average."""
    return series.ewm(span=period, adjust=False, min_periods=1).mean()


def sma_value(series: pd.Series, period: int) -> Optional[float]:
    """Last value of SMA; None if insufficient data."""
    if len(series) < period:
        return None
    return float(sma(series, period).iloc[-1])


def ema_value(series: pd.Series, period: int) -> Optional[float]:
    """Last value of EMA; None if insufficient data."""
    if len(series) < period:
        return None
    return float(ema(series, period).iloc[-1])


# ----- 3. Volume analysis -----
def volume_sma(series: pd.Series, period: int) -> Optional[float]:
    """Volume SMA over period (last value)."""
    return sma_value(series, period)


def volume_ratio(series: pd.Series, period: int = 20) -> Optional[float]:
    """Current volume / SMA(volume); > 1 means above average volume."""
    if len(series) < period:
        return None
    current = series.iloc[-1]
    avg = sma(series, period).iloc[-1]
    if avg == 0 or pd.isna(avg):
        return None
    return float(current / avg)


# ----- 4. Momentum indicators (RSI, MACD) -----
def rsi(series: pd.Series, period: int = 14) -> Optional[float]:
    """
    Relative Strength Index (RSI).
    RSI = 100 - (100 / (1 + RS)), RS = avg gain / avg loss (Wilder-style smoothing).
    Uses exponential moving average of gains/losses (alpha = 1/period).
    """
    if len(series) < period + 1:
        return None
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean().iloc[-1]
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean().iloc[-1]
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return float(100 - (100 / (1 + rs)))


def macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> Optional[dict[str, float]]:
    """
    MACD (Moving Average Convergence Divergence).
    Returns dict with macd_line, signal_line, histogram at the last bar.
    macd_line = EMA(fast) - EMA(slow); signal_line = EMA(macd_line, signal); histogram = macd - signal.
    """
    if len(series) < slow + signal:
        return None
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return {
        "macd_line": float(macd_line.iloc[-1]),
        "signal_line": float(signal_line.iloc[-1]),
        "histogram": float(histogram.iloc[-1]),
    }


# ----- Simple momentum (existing) -----
def compute_momentum(series: pd.Series, period: int = 10) -> Optional[float]:
    """Simple momentum: (current - period_ago) / period_ago * 100."""
    return compute_price_change_pct(series, period)


# ----- 5. Performance ranking -----
def rank_assets(
    rows: list[dict[str, Any]],
    by: str = "price_change_pct",
    ascending: bool = False,
) -> list[dict[str, Any]]:
    """
    Rank assets by a numeric field. Tie-break by symbol.
    Adds "rank" (1-based) to each row. Nulls sort last.
    """
    if not rows:
        return []
    valid = [r for r in rows if r.get(by) is not None]
    nulls = [r for r in rows if r.get(by) is None]
    valid.sort(key=lambda r: (r.get(by), r.get("symbol", "")), reverse=not ascending)
    for i, r in enumerate(valid, start=1):
        r = r.copy()
        r["rank"] = i
        valid[i - 1] = r
    for j, r in enumerate(nulls):
        r = r.copy()
        r["rank"] = None
        nulls[j] = r
    return valid + nulls


# ----- Orchestration: run analytics for all symbols -----
async def run_analytics(
    session: AsyncSession,
    window_hours: int = 24,
    include_indicators: bool = True,
) -> list[dict[str, Any]]:
    """
    Run full analytics for all symbols:
    Percentage change, SMA/EMA, volume ratio, RSI, MACD, momentum, and rank.
    Returns list of dicts; each includes rank when include_indicators=True.
    """
    symbols = await get_all_symbols(session)
    if not symbols:
        return []
    since = datetime.now(timezone.utc) - timedelta(hours=window_hours * 2)
    out: list[dict[str, Any]] = []
    for symbol in symbols:
        df = await get_price_history(session, symbol, limit=1000, since=since)
        if df.empty or len(df) < 2:
            out.append({
                "symbol": symbol,
                "price_change_pct": None,
                "volume_change_pct": None,
                "momentum": None,
                "current_price": None,
                "current_volume": None,
                "window_hours": window_hours,
                "sma_20": None,
                "ema_20": None,
                "volume_ratio_20": None,
                "rsi_14": None,
                "macd": None,
                "rank": None,
            })
            continue
        price = df["price"].astype(float)
        volume = df["volume"].astype(float)
        window_points = max(2, min(len(df) - 1, window_hours * 12))

        row: dict[str, Any] = {
            "symbol": symbol,
            "price_change_pct": compute_price_change_pct(price, window_points),
            "volume_change_pct": compute_volume_change_pct(volume, window_points),
            "momentum": compute_momentum(price, period=min(10, len(df) - 1)),
            "current_price": Decimal(str(price.iloc[-1])),
            "current_volume": Decimal(str(volume.iloc[-1])) if pd.notna(volume.iloc[-1]) else None,
            "window_hours": window_hours,
            "sma_20": None,
            "ema_20": None,
            "volume_ratio_20": None,
            "rsi_14": None,
            "macd": None,
            "rank": None,
        }
        if include_indicators:
            row["sma_20"] = sma_value(price, 20) if len(price) >= 20 else None
            row["ema_20"] = ema_value(price, 20) if len(price) >= 20 else None
            row["volume_ratio_20"] = volume_ratio(volume, 20) if len(volume) >= 20 else None
            row["rsi_14"] = rsi(price, 14)
            row["macd"] = macd(price, 12, 26, 9)
        out.append(row)

    if include_indicators:
        out = rank_assets(out, by="price_change_pct", ascending=False)
    return out


async def run_analytics_and_persist(
    session: AsyncSession,
    window_hours: int = 24,
) -> int:
    """
    Run analytics for all symbols and persist results to analytics_results.
    Persists core fields only (price_change_pct, volume_change_pct, momentum, etc.).
    Returns number of rows inserted.
    """
    rows = await run_analytics(session, window_hours=window_hours, include_indicators=False)
    if not rows:
        return 0
    now = datetime.now(timezone.utc)
    for r in rows:
        session.add(
            AnalyticsResult(
                symbol=r["symbol"],
                window_hours=window_hours,
                price_change_pct=r.get("price_change_pct"),
                volume_change_pct=r.get("volume_change_pct"),
                momentum=r.get("momentum"),
                current_price=r.get("current_price"),
                current_volume=r.get("current_volume"),
                computed_at=now,
            )
        )
    await session.flush()
    return len(rows)
