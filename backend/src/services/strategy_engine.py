"""
Strategy engine: thin wrapper over strategy.py for backward compatibility.

Delegates to StrategyFactory in strategy.py.
"""
from typing import Any

import pandas as pd

from src.services.strategy import StrategyFactory


def run_strategy(
    strategy_name: str,
    df: pd.DataFrame,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Run a named strategy on price DataFrame. Uses StrategyFactory."""
    return StrategyFactory.run(strategy_name, df, **kwargs)
