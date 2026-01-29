"""Market data endpoints.

GET  /api/v1/markets         - List all crypto assets
GET  /api/v1/markets/{symbol} - Specific asset details
POST /api/v1/markets/ingest - Trigger data ingestion
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlalchemy import and_, func, select

from src.api.schemas import MarketAssetWithLatestPrice
from src.api.v1.dependencies import DbSession, ValidatedSymbol
from src.core.cache import cache_delete, cache_get_json, cache_set_json
from src.core.database import AsyncSessionLocal
from src.models.market import CryptoAsset, MarketData
from src.services.data_ingestion import ingest_latest_prices

router = APIRouter()

CACHE_KEY_MARKETS = "markets:list"
CACHE_TTL_MARKETS_SEC = 60


async def _run_ingest_background() -> None:
    """Run ingest in a new session and invalidate cache."""
    async with AsyncSessionLocal() as session:
        try:
            await ingest_latest_prices(session)
            await session.commit()
        finally:
            await cache_delete(CACHE_KEY_MARKETS)


@router.get("", response_model=list[MarketAssetWithLatestPrice])
async def list_markets(db: DbSession) -> list:
    """List all crypto assets with latest price/volume. Cached 1 min. Single optimized query."""
    cached = await cache_get_json(CACHE_KEY_MARKETS)
    if cached is not None:
        return [MarketAssetWithLatestPrice.model_validate(x) for x in cached]

    # Single query: join assets with their latest market_data row (no N+1)
    latest_subq = (
        select(MarketData.asset_id, func.max(MarketData.timestamp).label("ts"))
        .group_by(MarketData.asset_id)
        .subquery()
    )
    stmt = (
        select(CryptoAsset, MarketData)
        .join(MarketData, CryptoAsset.id == MarketData.asset_id)
        .join(
            latest_subq,
            and_(
                MarketData.asset_id == latest_subq.c.asset_id,
                MarketData.timestamp == latest_subq.c.ts,
            ),
        )
        .order_by(CryptoAsset.symbol)
    )
    result = await db.execute(stmt)
    rows = result.all()
    out = [
        MarketAssetWithLatestPrice(
            id=a.id,
            symbol=a.symbol,
            name=a.name,
            coingecko_id=a.coingecko_id,
            created_at=a.created_at,
            updated_at=a.updated_at,
            latest_price=rec.price if rec else None,
            latest_volume=rec.volume if rec else None,
            latest_timestamp=rec.timestamp if rec else None,
        )
        for a, rec in rows
    ]
    await cache_set_json(
        CACHE_KEY_MARKETS,
        [r.model_dump(mode="json") for r in out],
        CACHE_TTL_MARKETS_SEC,
    )
    return out


@router.get("/{symbol}", response_model=MarketAssetWithLatestPrice)
async def get_market_by_symbol(
    db: DbSession,
    symbol: ValidatedSymbol,
) -> MarketAssetWithLatestPrice:
    """Specific asset details with latest price/volume."""
    result = await db.execute(
        select(CryptoAsset).where(CryptoAsset.symbol == symbol)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset not found: {symbol}")
    latest = await db.execute(
        select(MarketData)
        .where(MarketData.asset_id == asset.id)
        .order_by(MarketData.timestamp.desc())
        .limit(1)
    )
    rec = latest.scalar_one_or_none()
    return MarketAssetWithLatestPrice(
        id=asset.id,
        symbol=asset.symbol,
        name=asset.name,
        coingecko_id=asset.coingecko_id,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
        latest_price=rec.price if rec else None,
        latest_volume=rec.volume if rec else None,
        latest_timestamp=rec.timestamp if rec else None,
    )


@router.post("/ingest")
async def trigger_ingest(background_tasks: BackgroundTasks) -> dict:
    """Trigger ingestion in background; return immediately."""
    background_tasks.add_task(_run_ingest_background)
    return {"status": "accepted", "message": "Ingest started in background"}