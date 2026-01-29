"""Strategy endpoints."""
import json

from fastapi import APIRouter, Query
from sqlalchemy import distinct, select

from src.api.schemas import (
    StrategyRunRequest,
    StrategyRunSchema,
    StrategySignalSchema,
)
from src.api.v1.dependencies import DbSession
from src.models.market import MarketData
from src.models.strategy import StrategyRun, StrategySignal
from src.services.analytics import get_price_history
from src.services.strategy_engine import run_strategy

router = APIRouter()


@router.post("/run", response_model=StrategyRunSchema)
async def run_strategy_endpoint(
    db: DbSession,
    body: StrategyRunRequest | None = None,
) -> StrategyRunSchema:
    """Run the configured strategy on stored historical data; persist run and signals."""
    body = body or StrategyRunRequest()
    strategy_name = body.strategy_name
    limit = body.limit_per_symbol
    sym_result = await db.execute(select(distinct(MarketData.symbol)))
    symbols_list = [r[0] for r in sym_result.all()]
    if not symbols_list:
        run = StrategyRun(
            strategy_name=strategy_name,
            params_snapshot=json.dumps({"limit": limit}),
            status="completed",
        )
        db.add(run)
        await db.flush()
        return StrategyRunSchema(
            id=run.id,
            run_at=run.run_at,
            strategy_name=run.strategy_name,
            params_snapshot=run.params_snapshot,
            status=run.status,
            signals=[],
        )
    run = StrategyRun(
        strategy_name=strategy_name,
        params_snapshot=json.dumps({"limit": limit}),
        status="completed",
    )
    db.add(run)
    await db.flush()
    signals_out: list[StrategySignalSchema] = []
    for symbol in symbols_list:
        df = await get_price_history(db, symbol, limit=limit)
        if df.empty:
            continue
        result_list = run_strategy(strategy_name, df)
        for r in result_list:
            sig = StrategySignal(
                run_id=run.id,
                symbol=symbol,
                signal=r["signal"],
                price_at_signal=str(r["price"]),
                reason=r.get("reason"),
            )
            db.add(sig)
            await db.flush()
            signals_out.append(
                StrategySignalSchema(
                    symbol=symbol,
                    signal=r["signal"],
                    price_at_signal=str(r["price"]),
                    reason=r.get("reason"),
                    created_at=sig.created_at,
                )
            )
    return StrategyRunSchema(
        id=run.id,
        run_at=run.run_at,
        strategy_name=run.strategy_name,
        params_snapshot=run.params_snapshot,
        status=run.status,
        signals=signals_out,
    )


@router.get("/results", response_model=list[StrategyRunSchema])
async def get_strategy_results(
    db: DbSession,
    limit: int = Query(10, ge=1, le=50),
) -> list:
    """Return latest strategy runs with their signals."""
    q = (
        select(StrategyRun)
        .order_by(StrategyRun.run_at.desc())
        .limit(limit)
    )
    result = await db.execute(q)
    runs = result.scalars().all()
    out = []
    for run in runs:
        sig_result = await db.execute(
            select(StrategySignal)
            .where(StrategySignal.run_id == run.id)
            .order_by(StrategySignal.symbol)
        )
        signals = sig_result.scalars().all()
        out.append(
            StrategyRunSchema(
                id=run.id,
                run_at=run.run_at,
                strategy_name=run.strategy_name,
                params_snapshot=run.params_snapshot,
                status=run.status,
                signals=[
                    StrategySignalSchema(
                        symbol=s.symbol,
                        signal=s.signal,
                        price_at_signal=s.price_at_signal,
                        reason=s.reason,
                        created_at=s.created_at,
                    )
                    for s in signals
                ],
            )
        )
    return out
