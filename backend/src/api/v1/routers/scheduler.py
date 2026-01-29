"""Scheduler config endpoint: expose job intervals (mirrors src/tasks/scheduler)."""
from fastapi import APIRouter

from src.core.config import get_settings

router = APIRouter()


@router.get("/config")
async def get_scheduler_config() -> dict:
    """
    Return scheduler job intervals (from config). Read-only.
    Mirrors backend src/tasks/scheduler.py job definitions.
    """
    s = get_settings()
    return {
        "market_data_refresh_minutes": s.fetch_interval_minutes,
        "analytics_computation_minutes": s.analytics_interval_minutes,
        "strategy_reevaluation_minutes": s.strategy_interval_minutes,
        "database_cleanup_hours": s.cleanup_interval_hours,
        "market_data_retention_days": s.market_data_retention_days,
        "analytics_results_retention_days": s.analytics_results_retention_days,
        "strategy_runs_retention_days": s.strategy_runs_retention_days,
    }
