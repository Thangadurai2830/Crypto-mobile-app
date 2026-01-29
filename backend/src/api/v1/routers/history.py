"""Historical data endpoint.

GET /api/v1/history/{symbol} - Historical price/volume for symbol
"""
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from src.api.schemas import PriceRecordSchema
from src.api.v1.dependencies import DbSession, ValidatedSymbol
from src.models.market import MarketData

router = APIRouter()


@router.get("/{symbol}", response_model=list[PriceRecordSchema])
async def get_history(
    db: DbSession,
    symbol: ValidatedSymbol,
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
) -> list:
    """Historical price/volume data for the given symbol."""
    result = await db.execute(
        select(MarketData)
        .where(MarketData.symbol == symbol)
        .order_by(MarketData.timestamp.desc())
        .limit(limit)
    )
    rows = result.scalars().all()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No history for: {symbol}")
    return [
        PriceRecordSchema(symbol=r.symbol, price=r.price, volume=r.volume, timestamp=r.timestamp)
        for r in rows
    ]
