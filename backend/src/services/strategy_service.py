"""Strategy run and persist: shared by API and scheduler."""
import json
from sqlalchemy import distinct, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.market import MarketData
from src.models.strategy import StrategyRun, StrategySignal
from src.services.analytics import get_price_history
from src.services.strategy_engine import run_strategy


async def run_strategy_and_persist(
    session: AsyncSession,
    strategy_name: str | None = None,
    limit_per_symbol: int | None = None,
) -> int:
    """
    Run the configured strategy on stored historical data; persist run and signals.
    Returns number of signals created. Used by scheduler and API.
    """
    strategy_name = strategy_name or "ma_crossover"
    limit = limit_per_symbol or 100
    sym_result = await session.execute(select(distinct(MarketData.symbol)))
    symbols_list = [r[0] for r in sym_result.all()]
    run = StrategyRun(
        strategy_name=strategy_name,
        params_snapshot=json.dumps({"limit": limit}),
        status="completed",
    )
    session.add(run)
    await session.flush()
    count = 0
    for symbol in symbols_list:
        df = await get_price_history(session, symbol, limit=limit)
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
            session.add(sig)
            count += 1
    await session.flush()
    return count
