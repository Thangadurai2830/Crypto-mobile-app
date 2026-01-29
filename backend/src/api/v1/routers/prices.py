"""Current price endpoint.

GET /api/v1/prices/{symbol} - Current price for symbol
"""
from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from src.api.schemas import PriceRecordSchema
from src.api.v1.dependencies import DbSession, ValidatedSymbol
from src.models.market import MarketData

router = APIRouter()


@router.get("/{symbol}", response_model=PriceRecordSchema)
async def get_current_price(
    db: DbSession,
    symbol: ValidatedSymbol,
) -> PriceRecordSchema:
    """Current price (and volume) for the given symbol."""
    result = await db.execute(
        select(MarketData)
        .where(MarketData.symbol == symbol)
        .order_by(MarketData.timestamp.desc())
        .limit(1)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail=f"No price data for: {symbol}")
    return PriceRecordSchema(
        symbol=row.symbol,
        price=row.price,
        volume=row.volume,
        timestamp=row.timestamp,
    )
