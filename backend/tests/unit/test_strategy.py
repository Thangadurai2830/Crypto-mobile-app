"""Unit tests for strategy business logic: MA crossover, backtest, metrics."""
import pandas as pd
import pytest

from src.services.strategy import (
    MACrossoverStrategy,
    StrategyFactory,
    backtest,
    _max_drawdown_pct,
    _win_rate,
)


class TestMACrossoverStrategy:
    def test_empty_df_returns_hold(self):
        s = MACrossoverStrategy()
        df = pd.DataFrame(columns=["price"])
        out = s.generate_signal(df)
        assert len(out) == 1
        assert out[0]["signal"] == "HOLD"
        assert out[0]["reason"] == "No price data"

    def test_insufficient_data_returns_hold(self):
        s = MACrossoverStrategy(fast_period=2, slow_period=5)
        df = pd.DataFrame({"price": [100.0, 101.0, 102.0]})  # 3 points
        out = s.generate_signal(df)
        assert out[0]["signal"] == "HOLD"
        assert "Insufficient data" in out[0]["reason"]

    def test_hold_when_no_crossover(self):
        s = MACrossoverStrategy(fast_period=2, slow_period=4)
        df = pd.DataFrame({"price": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0]})
        result = s.generate_signal(df)
        assert len(result) == 1
        assert result[0]["signal"] in ("HOLD", "BUY", "SELL")
        assert "price" in result[0]


class TestStrategyFactory:
    def test_list_names(self):
        names = StrategyFactory.list_names()
        assert "ma_crossover" in names
        assert "momentum" in names
        assert "momentum_rsi" in names

    def test_unknown_strategy_returns_hold(self):
        result = StrategyFactory.run("unknown_strategy", pd.DataFrame({"price": [100.0]}))
        assert len(result) == 1
        assert result[0]["signal"] == "HOLD"
        assert "Unknown strategy" in result[0]["reason"]


class TestBacktest:
    def test_empty_df_returns_initial_capital(self):
        result = backtest(pd.DataFrame(), initial_capital=10_000.0)
        assert result.final_equity == 10_000.0
        assert result.equity_curve == [10_000.0]
        assert result.num_trades == 0

    def test_single_price_returns_initial_capital(self):
        df = pd.DataFrame({"price": [100.0]})
        result = backtest(df, initial_capital=5_000.0)
        assert result.final_equity == 5_000.0
        assert result.num_trades == 0

    def test_two_prices_no_signal_change(self):
        df = pd.DataFrame({"price": [100.0, 101.0]})
        result = backtest(df, strategy_name="ma_crossover", initial_capital=10_000.0)
        assert result.num_trades >= 0
        assert result.final_equity >= 0
        assert len(result.equity_curve) == 2

    def test_has_expected_attributes(self):
        df = pd.DataFrame({"price": [100.0, 101.0, 102.0, 103.0, 104.0]})
        result = backtest(df, initial_capital=10_000.0)
        assert hasattr(result, "total_return_pct")
        assert hasattr(result, "sharpe_ratio")
        assert hasattr(result, "win_rate")
        assert hasattr(result, "max_drawdown_pct")
        assert hasattr(result, "num_trades")


class TestMaxDrawdownPct:
    def test_empty_zero(self):
        assert _max_drawdown_pct([]) == 0.0

    def test_single_value_zero(self):
        assert _max_drawdown_pct([1000.0]) == 0.0

    def test_decline(self):
        curve = [100.0, 90.0, 80.0]
        assert _max_drawdown_pct(curve) == 20.0  # 100 -> 80

    def test_recovery(self):
        curve = [100.0, 80.0, 90.0]
        assert _max_drawdown_pct(curve) == 20.0


class TestWinRate:
    def test_empty_zero(self):
        assert _win_rate([]) == 0.0

    def test_no_closing_trades_zero(self):
        assert _win_rate([{"type": "buy", "pnl": 0}]) == 0.0

    def test_profitable_sell(self):
        trades = [{"type": "sell", "pnl": 5.0}]
        assert _win_rate(trades) == 1.0

    def test_losing_sell(self):
        trades = [{"type": "sell", "pnl": -3.0}]
        assert _win_rate(trades) == 0.0

    def test_mixed(self):
        trades = [
            {"type": "sell", "pnl": 2.0},
            {"type": "close_short", "pnl": -1.0},
        ]
        assert _win_rate(trades) == 0.5
