"""Unit tests for security: validate_symbol, validate_strategy_name."""
import pytest

from src.core.security import validate_symbol, validate_strategy_name


class TestValidateSymbol:
    def test_valid_uppercase(self):
        assert validate_symbol("BTC") == "BTC"
        assert validate_symbol("ETH") == "ETH"

    def test_valid_lowercase_normalized(self):
        assert validate_symbol("btc") == "BTC"
        assert validate_symbol("eth") == "ETH"

    def test_valid_with_hyphen_dot(self):
        assert validate_symbol("wrapped-btc") == "WRAPPED-BTC"
        assert validate_symbol("USDT.T") == "USDT.T"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="1–20 characters"):
            validate_symbol("")
        with pytest.raises(ValueError, match="1–20 characters"):
            validate_symbol("   ")

    def test_too_long_raises(self):
        with pytest.raises(ValueError, match="1–20 characters"):
            validate_symbol("A" * 21)

    def test_invalid_chars_raises(self):
        with pytest.raises(ValueError, match="alphanumeric"):
            validate_symbol("BT C")
        with pytest.raises(ValueError, match="alphanumeric"):
            validate_symbol("BTC/USD")
        with pytest.raises(ValueError, match="alphanumeric"):
            validate_symbol("<script>")

    def test_strips_whitespace(self):
        assert validate_symbol("  btc  ") == "BTC"


class TestValidateStrategyName:
    def test_allowed_names(self):
        assert validate_strategy_name("ma_crossover") == "ma_crossover"
        assert validate_strategy_name("momentum") == "momentum"
        assert validate_strategy_name("momentum_rsi") == "momentum_rsi"

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="one of"):
            validate_strategy_name("unknown")
        with pytest.raises(ValueError, match="one of"):
            validate_strategy_name("ma-crossover")
