"""Analytics endpoints."""
from datetime import datetime, timezone

from fastapi import APIRouter, Query

from src.api.schemas import AnalyticsResponse, AssetAnalyticsSchema, MacdSchema
from src.api.v1.dependencies import DbSession
from src.core.cache import cache_get_json, cache_set_json
from src.services.analytics import run_analytics

router = APIRouter()

CACHE_KEY_ANALYTICS = "analytics"
CACHE_TTL_ANALYTICS_SEC = 60


@router.get("", response_model=AnalyticsResponse)
async def get_analytics(
    db: DbSession,
    window_hours: int = Query(24, ge=1, le=168, description="Window for change % (hours)"),
) -> AnalyticsResponse:
    """Return analytics: price change %, volume change %, momentum, SMA/EMA, RSI, MACD, rank per asset. Cached 1 min."""
    cached = await cache_get_json(f"{CACHE_KEY_ANALYTICS}:{window_hours}")
    if cached is not None:
        return AnalyticsResponse.model_validate(cached)

    rows = await run_analytics(db, window_hours=window_hours, include_indicators=True)
    assets = [
        AssetAnalyticsSchema(
            symbol=r["symbol"],
            price_change_pct=r.get("price_change_pct"),
            volume_change_pct=r.get("volume_change_pct"),
            momentum=r.get("momentum"),
            current_price=r.get("current_price"),
            current_volume=r.get("current_volume"),
            window_hours=r["window_hours"],
            sma_20=r.get("sma_20"),
            ema_20=r.get("ema_20"),
            volume_ratio_20=r.get("volume_ratio_20"),
            rsi_14=r.get("rsi_14"),
            macd=MacdSchema(**m) if (m := r.get("macd")) else None,
            rank=r.get("rank"),
        )
        for r in rows
    ]
    resp = AnalyticsResponse(
        window_hours=window_hours,
        computed_at=datetime.now(timezone.utc),
        assets=assets,
    )
    await cache_set_json(
        f"{CACHE_KEY_ANALYTICS}:{window_hours}",
        resp.model_dump(mode="json"),
        CACHE_TTL_ANALYTICS_SEC,
    )
    return resp
