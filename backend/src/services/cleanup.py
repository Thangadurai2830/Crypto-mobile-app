"""Database cleanup: remove old market data, analytics results, strategy runs."""
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.models.analytics import AnalyticsResult
from src.models.market import MarketData
from src.models.strategy import StrategyRun

logger = logging.getLogger(__name__)
settings = get_settings()


async def cleanup_old_data(session: AsyncSession) -> dict[str, int]:
    """
    Delete old records based on retention settings.
    Returns dict with deleted counts: market_data, analytics_results, strategy_runs.
    Strategy signals are deleted by DB CASCADE when runs are deleted.
    """
    now = datetime.now(timezone.utc)
    result: dict[str, int] = {"market_data": 0, "analytics_results": 0, "strategy_runs": 0}

    # Old market data (price_records)
    retain_market = now - timedelta(days=settings.market_data_retention_days)
    stmt = delete(MarketData).where(MarketData.timestamp < retain_market)
    r = await session.execute(stmt)
    result["market_data"] = r.rowcount or 0
    if result["market_data"]:
        logger.info("Cleanup: deleted %s old market_data rows", result["market_data"])

    # Old analytics results
    retain_analytics = now - timedelta(days=settings.analytics_results_retention_days)
    stmt = delete(AnalyticsResult).where(AnalyticsResult.computed_at < retain_analytics)
    r = await session.execute(stmt)
    result["analytics_results"] = r.rowcount or 0
    if result["analytics_results"]:
        logger.info("Cleanup: deleted %s old analytics_results rows", result["analytics_results"])

    # Old strategy runs (DB CASCADE deletes strategy_signals)
    retain_runs = now - timedelta(days=settings.strategy_runs_retention_days)
    stmt = delete(StrategyRun).where(StrategyRun.run_at < retain_runs)
    r = await session.execute(stmt)
    result["strategy_runs"] = r.rowcount or 0
    if result["strategy_runs"]:
        logger.info("Cleanup: deleted %s old strategy_runs (signals cascaded)", result["strategy_runs"])

    await session.flush()
    return result
