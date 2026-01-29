"""Cleanup endpoint: trigger backend cleanup service (old market data, analytics, strategy runs)."""
from fastapi import APIRouter, Depends

from src.api.v1.dependencies import DbSession
from src.services.cleanup import cleanup_old_data

router = APIRouter()


@router.post("")
async def trigger_cleanup(db: DbSession) -> dict:
    """
    Run cleanup_old_data: delete old market_data, analytics_results, strategy_runs
    per retention settings. Returns deleted counts.
    """
    result = await cleanup_old_data(db)
    await db.commit()
    return {"status": "ok", "deleted": result}
