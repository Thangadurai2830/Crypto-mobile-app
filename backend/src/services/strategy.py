"""
Trading Strategy Implementation:

1. Moving Average Crossover Strategy
   - Fast MA (7-day) vs Slow MA (21-day)
   - Generate BUY/SELL/HOLD signals

2. Momentum Threshold Strategy (RSI-based)
   - RSI-based signals with volume confirmation

3. Strategy Factory Pattern for extensibility
4. Backtesting framework
5. Performance metrics calculation
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Protocol

import pandas as pd

from src.core.config import get_settings
from src.services.analytics import rsi, volume_ratio

settings = get_settings()

SIGNAL_BUY = "BUY"
SIGNAL_SELL = "SELL"
SIGNAL_HOLD = "HOLD"


# ----- Strategy protocol and base -----
class StrategyProtocol(Protocol):
    """Protocol for strategy: generate_signal(df) -> list[dict]."""

    def generate_signal(self, df: pd.DataFrame, **kwargs: Any) -> list[dict[str, Any]]:
        ...


class BaseStrategy(ABC):
    """Base class for strategies."""

    name: str = "base"

    @abstractmethod
    def generate_signal(self, df: pd.DataFrame, **kwargs: Any) -> list[dict[str, Any]]:
        """Return list of one dict: {signal, reason, price}."""
        ...


# ----- 1. Moving Average Crossover Strategy -----
class MACrossoverStrategy(BaseStrategy):
    """
    Fast MA (7-day) vs Slow MA (21-day).
    BUY when fast MA crosses above slow MA; SELL when fast crosses below; else HOLD.
    """

    name = "ma_crossover"

    def __init__(
        self,
        fast_period: int | None = None,
        slow_period: int | None = None,
    ):
        self.fast_period = fast_period or settings.ma_fast_period
        self.slow_period = slow_period or settings.ma_slow_period

    def generate_signal(self, df: pd.DataFrame, **kwargs: Any) -> list[dict[str, Any]]:
        if df.empty or "price" not in df.columns:
            return [{"signal": SIGNAL_HOLD, "reason": "No price data", "price": 0.0}]
        series = df["price"].astype(float)
        if len(series) < self.slow_period + 1:
            return [{
                "signal": SIGNAL_HOLD,
                "reason": f"Insufficient data for MA({self.fast_period}/{self.slow_period})",
                "price": float(series.iloc[-1]),
            }]
        fast_ma = series.rolling(self.fast_period, min_periods=1).mean()
        slow_ma = series.rolling(self.slow_period, min_periods=1).mean()
        prev_above = fast_ma.iloc[-2] > slow_ma.iloc[-2]
        curr_above = fast_ma.iloc[-1] > slow_ma.iloc[-1]
        last_price = float(series.iloc[-1])
        if not prev_above and curr_above:
            return [{
                "signal": SIGNAL_BUY,
                "reason": f"MA crossover: fast MA ({self.fast_period}) crossed above slow MA ({self.slow_period})",
                "price": last_price,
            }]
        if prev_above and not curr_above:
            return [{
                "signal": SIGNAL_SELL,
                "reason": f"MA crossover: fast MA ({self.fast_period}) crossed below slow MA ({self.slow_period})",
                "price": last_price,
            }]
        return [{"signal": SIGNAL_HOLD, "reason": "No MA crossover", "price": last_price}]


# ----- 2. Momentum Threshold Strategy (RSI + volume confirmation) -----
class MomentumRSIStrategy(BaseStrategy):
    """
    RSI-based signals with volume confirmation.
    BUY when RSI < oversold (and optionally volume above average); SELL when RSI > overbought; else HOLD.
    """

    name = "momentum_rsi"

    def __init__(
        self,
        rsi_period: int | None = None,
        overbought: float | None = None,
        oversold: float | None = None,
        volume_ratio_min: float | None = None,
    ):
        self.rsi_period = rsi_period or settings.rsi_period
        self.overbought = overbought or settings.rsi_overbought
        self.oversold = oversold or settings.rsi_oversold
        self.volume_ratio_min = volume_ratio_min if volume_ratio_min is not None else settings.volume_confirmation_ratio

    def generate_signal(self, df: pd.DataFrame, **kwargs: Any) -> list[dict[str, Any]]:
        if df.empty or "price" not in df.columns:
            return [{"signal": SIGNAL_HOLD, "reason": "No price data", "price": 0.0}]
        price = df["price"].astype(float)
        last_price = float(price.iloc[-1])
        if len(price) < self.rsi_period + 1:
            return [{"signal": SIGNAL_HOLD, "reason": "Insufficient data for RSI", "price": last_price}]
        rsi_val = rsi(price, self.rsi_period)
        if rsi_val is None:
            return [{"signal": SIGNAL_HOLD, "reason": "RSI not available", "price": last_price}]
        volume_ok = True
        if "volume" in df.columns and self.volume_ratio_min > 0:
            vol = df["volume"].astype(float)
            vr = volume_ratio(vol, 20)
            volume_ok = vr is not None and vr >= self.volume_ratio_min
        if rsi_val <= self.oversold and volume_ok:
            return [{
                "signal": SIGNAL_BUY,
                "reason": f"RSI oversold ({rsi_val:.1f} <= {self.oversold})" + (" + volume confirmation" if volume_ok else ""),
                "price": last_price,
            }]
        if rsi_val >= self.overbought and volume_ok:
            return [{
                "signal": SIGNAL_SELL,
                "reason": f"RSI overbought ({rsi_val:.1f} >= {self.overbought})" + (" + volume confirmation" if volume_ok else ""),
                "price": last_price,
            }]
        return [{"signal": SIGNAL_HOLD, "reason": f"RSI neutral ({rsi_val:.1f})", "price": last_price}]


# ----- Legacy momentum (percent threshold) -----
class MomentumThresholdStrategy(BaseStrategy):
    """Momentum % threshold: BUY/SELL when price change % exceeds threshold."""

    name = "momentum"

    def __init__(self, period: int = 10, threshold_pct: float | None = None):
        self.period = period
        self.threshold_pct = threshold_pct or settings.momentum_threshold_pct

    def generate_signal(self, df: pd.DataFrame, **kwargs: Any) -> list[dict[str, Any]]:
        if df.empty or len(df) < self.period + 1:
            last = float(df["price"].iloc[-1]) if not df.empty and "price" in df.columns else 0.0
            return [{"signal": SIGNAL_HOLD, "reason": "Insufficient data", "price": last}]
        series = df["price"].astype(float)
        momentum = (series.iloc[-1] - series.iloc[-1 - self.period]) / series.iloc[-1 - self.period] * 100
        last_price = float(series.iloc[-1])
        if momentum >= self.threshold_pct:
            return [{"signal": SIGNAL_BUY, "reason": f"Momentum {momentum:.2f}% >= {self.threshold_pct}%", "price": last_price}]
        if momentum <= -self.threshold_pct:
            return [{"signal": SIGNAL_SELL, "reason": f"Momentum {momentum:.2f}% <= -{self.threshold_pct}%", "price": last_price}]
        return [{"signal": SIGNAL_HOLD, "reason": f"Momentum {momentum:.2f}% within ±{self.threshold_pct}%", "price": last_price}]


# ----- 3. Strategy Factory -----
class StrategyFactory:
    """Factory for strategy registration and lookup."""

    _strategies: dict[str, BaseStrategy] = {}

    @classmethod
    def register(cls, name: str, strategy: BaseStrategy | type[BaseStrategy]) -> None:
        if isinstance(strategy, type):
            strategy = strategy()
        cls._strategies[name] = strategy

    @classmethod
    def get(cls, name: str) -> BaseStrategy | None:
        return cls._strategies.get(name)

    @classmethod
    def list_names(cls) -> list[str]:
        return list(cls._strategies.keys())

    @classmethod
    def run(cls, name: str, df: pd.DataFrame, **kwargs: Any) -> list[dict[str, Any]]:
        s = cls.get(name)
        if s is None:
            return [{"signal": SIGNAL_HOLD, "reason": f"Unknown strategy: {name}", "price": 0.0}]
        return s.generate_signal(df, **kwargs)


# Register built-in strategies
StrategyFactory.register("ma_crossover", MACrossoverStrategy())
StrategyFactory.register("momentum", MomentumThresholdStrategy())
StrategyFactory.register("momentum_rsi", MomentumRSIStrategy())


# ----- 4. Backtesting -----
@dataclass
class BacktestResult:
    """Result of a backtest run."""

    trades: list[dict[str, Any]] = field(default_factory=list)
    equity_curve: list[float] = field(default_factory=list)
    total_return_pct: float = 0.0
    sharpe_ratio: float = 0.0
    win_rate: float = 0.0
    max_drawdown_pct: float = 0.0
    num_trades: int = 0
    final_equity: float = 0.0


def backtest(
    df: pd.DataFrame,
    strategy_name: str = "ma_crossover",
    initial_capital: float = 10_000.0,
    position_size_pct: float = 1.0,
) -> BacktestResult:
    """
    Backtest a strategy on historical price data.
    Assumes df has 'price' (and optionally 'volume'), sorted by time ascending.
    Simulates: at each bar, run strategy on history up to that bar; if signal changes to BUY/SELL, adjust position.
    Simplified: we track position (-1, 0, 1) and equity. Each bar we have position * (price change) P&L.
    """
    result = BacktestResult()
    if df.empty or len(df) < 2 or "price" not in df.columns:
        result.equity_curve = [initial_capital]
        result.final_equity = initial_capital
        return result
    price = df["price"].astype(float)
    equity = initial_capital
    position = 0  # -1 short, 0 flat, 1 long
    entry_price: float = 0.0
    trades: list[dict[str, Any]] = []
    equity_curve: list[float] = [initial_capital]
    prev_signal = SIGNAL_HOLD
    for i in range(1, len(price)):
        window = df.iloc[: i + 1].copy()
        sigs = StrategyFactory.run(strategy_name, window)
        signal = sigs[0]["signal"] if sigs else SIGNAL_HOLD
        p = price.iloc[i]
        p_prev = price.iloc[i - 1]
        ret_pct = (p - p_prev) / p_prev if p_prev else 0
        if position == 1:
            equity *= 1 + ret_pct * position_size_pct
        elif position == -1:
            equity *= 1 - ret_pct * position_size_pct
        equity_curve.append(equity)
        if signal == SIGNAL_BUY and position != 1:
            if position == -1:
                pnl = (entry_price - p) / entry_price * 100 if entry_price else 0
                trades.append({"type": "close_short", "price": p, "equity": equity, "pnl": pnl})
            position = 1
            entry_price = p
            if prev_signal != SIGNAL_BUY:
                trades.append({"type": "buy", "price": p, "equity": equity, "pnl": 0})
        elif signal == SIGNAL_SELL and position != -1:
            if position == 1:
                pnl = (p - entry_price) / entry_price * 100 if entry_price else 0
                trades.append({"type": "sell", "price": p, "equity": equity, "pnl": pnl})
            position = -1
            entry_price = p
            if prev_signal != SIGNAL_SELL:
                trades.append({"type": "open_short", "price": p, "equity": equity, "pnl": 0})
        elif signal == SIGNAL_HOLD and position != 0:
            pass
        prev_signal = signal
    result.equity_curve = equity_curve
    result.final_equity = equity
    result.trades = trades
    result.num_trades = len(trades)
    result.total_return_pct = (equity - initial_capital) / initial_capital * 100 if initial_capital else 0
    result.max_drawdown_pct = _max_drawdown_pct(equity_curve)
    result.sharpe_ratio = _sharpe_ratio(equity_curve)
    result.win_rate = _win_rate(trades)
    return result


def _max_drawdown_pct(equity_curve: list[float]) -> float:
    if not equity_curve:
        return 0.0
    peak = equity_curve[0]
    max_dd = 0.0
    for e in equity_curve:
        if e > peak:
            peak = e
        dd = (peak - e) / peak * 100 if peak else 0
        if dd > max_dd:
            max_dd = dd
    return max_dd


def _sharpe_ratio(equity_curve: list[float], risk_free_rate: float = 0.0) -> float:
    if len(equity_curve) < 2:
        return 0.0
    returns = []
    for i in range(1, len(equity_curve)):
        r = (equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1] if equity_curve[i - 1] else 0
        returns.append(r)
    if not returns:
        return 0.0
    mean_ret = sum(returns) / len(returns)
    variance = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
    std = variance ** 0.5
    if std == 0:
        return 0.0
    return (mean_ret - risk_free_rate / 252) / std * (252 ** 0.5)


def _win_rate(trades: list[dict[str, Any]]) -> float:
    """Win rate: fraction of closed trades (sell/close_short) that are profitable."""
    closing = [t for t in trades if t.get("type") in ("sell", "close_short")]
    if not closing:
        return 0.0
    profitable = sum(1 for t in closing if t.get("pnl", 0) > 0)
    return profitable / len(closing)


# ----- 5. Performance metrics (standalone) -----
def performance_metrics(
    equity_curve: list[float],
    trades: list[dict[str, Any]],
    initial_capital: float,
) -> dict[str, float]:
    """Compute performance metrics from equity curve and trades."""
    final = equity_curve[-1] if equity_curve else initial_capital
    return {
        "total_return_pct": (final - initial_capital) / initial_capital * 100 if initial_capital else 0,
        "max_drawdown_pct": _max_drawdown_pct(equity_curve),
        "sharpe_ratio": _sharpe_ratio(equity_curve),
        "win_rate": _win_rate(trades),
        "num_trades": len(trades),
        "final_equity": final,
    }
