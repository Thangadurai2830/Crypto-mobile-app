"""
API v1 package.

Endpoint design:
  GET     /api/v1/markets           - List all crypto assets
  GET     /api/v1/markets/{symbol}  - Specific asset details
  POST    /api/v1/markets/ingest   - Trigger data ingestion (backend data_ingestion)
  GET     /api/v1/prices/{symbol}  - Current price
  GET     /api/v1/history/{symbol}  - Historical data
  GET     /api/v1/analytics         - Computed analytics (backend analytics.run_analytics)
  POST    /api/v1/strategy/run      - Run strategy (backend strategy_engine + strategy_service)
  GET     /api/v1/strategy/results  - Strategy results
  POST    /api/v1/cleanup          - Trigger cleanup (backend cleanup.cleanup_old_data)
  GET     /api/v1/scheduler/config - Scheduler job intervals (backend tasks/scheduler)
  GET     /api/v1/health           - Health check

When API_KEY_ENABLED=true, all /v1 routes require X-API-Key header (current or previous key for rotation).
"""
from typing import Annotated

from fastapi import APIRouter, Depends

from src.api.v1.routers import analytics, cleanup, history, market, prices, scheduler, strategy
from src.core.security import require_api_key

api_router = APIRouter(
    dependencies=[Depends(require_api_key)],
)

api_router.include_router(market.router, prefix="/markets", tags=["markets"])
api_router.include_router(prices.router, prefix="/prices", tags=["prices"])
api_router.include_router(history.router, prefix="/history", tags=["history"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(strategy.router, prefix="/strategy", tags=["strategy"])
api_router.include_router(cleanup.router, prefix="/cleanup", tags=["cleanup"])
api_router.include_router(scheduler.router, prefix="/scheduler", tags=["scheduler"])


@api_router.get("/health")
async def health() -> dict:
    """Health check."""
    return {"status": "ok"}
