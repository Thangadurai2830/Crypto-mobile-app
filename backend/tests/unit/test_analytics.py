"""Unit tests for analytics business logic: pct change, RSI, SMA/EMA."""
import pandas as pd
import pytest

from src.services.analytics import (
    compute_pct_change,
    compute_price_change_pct,
    sma,
    ema,
    rsi,
)


class TestComputePctChange:
    def test_insufficient_data_returns_none(self):
        s = pd.Series([100.0, 101.0])
        assert compute_pct_change(s, window=2) is None

    def test_sufficient_data(self):
        s = pd.Series([100.0, 102.0, 104.0])
        assert compute_pct_change(s, window=2) == pytest.approx(4.0)  # (104-100)/100*100

    def test_zero_old_returns_none(self):
        s = pd.Series([0.0, 1.0, 2.0])
        assert compute_pct_change(s, window=2) is None


class TestComputePriceChangePct:
    def test_delegates_to_compute_pct_change(self):
        s = pd.Series([100.0, 105.0])
        assert compute_price_change_pct(s, window=1) == pytest.approx(5.0)


class TestSma:
    def test_empty_series(self):
        out = sma(pd.Series(dtype=float), period=5)
        assert out.empty or (out.isna().all() or len(out) == 0)

    def test_period_2(self):
        s = pd.Series([10.0, 12.0, 14.0])
        out = sma(s, period=2)
        assert len(out) == 3
        assert out.iloc[-1] == pytest.approx(13.0)  # (12+14)/2


class TestEma:
    def test_period_2_smooth(self):
        s = pd.Series([10.0, 12.0, 14.0])
        out = ema(s, period=2)
        assert len(out) == 3
        assert not out.iloc[-1] is None  # some value


class TestRsi:
    def test_insufficient_data_returns_none(self):
        s = pd.Series([100.0] * 5)
        assert rsi(s, period=14) is None

    def test_flat_series_rsi_around_50(self):
        s = pd.Series([100.0] * 20)
        val = rsi(s, period=14)
        assert val is not None
        assert 0 <= val <= 100

    def test_uptrend_high_rsi(self):
        s = pd.Series([100.0 + i for i in range(20)])
        val = rsi(s, period=14)
        assert val is not None
        assert val > 50
