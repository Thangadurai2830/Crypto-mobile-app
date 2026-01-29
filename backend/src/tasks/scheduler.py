"""
Configure APScheduler for:

1. Market data refresh every 5 minutes (configurable)
2. Analytics computation every 15 minutes (configurable)
3. Strategy re-evaluation every hour (configurable)
4. Database cleanup jobs (configurable interval and retention)
"""
import logging
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from src.core.config import get_settings
from src.core.database import AsyncSessionLocal
from src.services.analytics import run_analytics_and_persist
from src.services.cleanup import cleanup_old_data
from src.services.data_ingestion import ingest_latest_prices
from src.services.strategy_service import run_strategy_and_persist

logger = logging.getLogger(__name__)
_scheduler: AsyncIOScheduler | None = None


async def _job_market_data_refresh() -> None:
    """Job 1: Fetch and store latest market prices (every N minutes)."""
    job_id = "market_data_refresh"
    logger.info("Scheduled job started: %s", job_id)
    try:
        async with AsyncSessionLocal() as session:
            count = await ingest_latest_prices(session)
            await session.commit()
        logger.info("Scheduled job finished: %s, records_ingested=%s", job_id, count)
    except Exception as e:
        logger.exception("Scheduled job failed: %s, error=%s", job_id, e)


async def _job_analytics_computation() -> None:
    """Job 2: Compute analytics and persist to analytics_results (every N minutes)."""
    job_id = "analytics_computation"
    logger.info("Scheduled job started: %s", job_id)
    try:
        settings = get_settings()
        async with AsyncSessionLocal() as session:
            count = await run_analytics_and_persist(
                session,
                window_hours=settings.default_price_window_hours,
            )
            await session.commit()
        logger.info("Scheduled job finished: %s, rows_persisted=%s", job_id, count)
    except Exception as e:
        logger.exception("Scheduled job failed: %s, error=%s", job_id, e)


async def _job_strategy_reevaluation() -> None:
    """Job 3: Run strategy and persist signals (every N minutes)."""
    job_id = "strategy_reevaluation"
    logger.info("Scheduled job started: %s", job_id)
    try:
        async with AsyncSessionLocal() as session:
            count = await run_strategy_and_persist(
                session,
                strategy_name="ma_crossover",
                limit_per_symbol=100,
            )
            await session.commit()
        logger.info("Scheduled job finished: %s, signals_created=%s", job_id, count)
    except Exception as e:
        logger.exception("Scheduled job failed: %s, error=%s", job_id, e)


async def _job_database_cleanup() -> None:
    """Job 4: Delete old market_data, analytics_results, strategy_runs (every N hours)."""
    job_id = "database_cleanup"
    logger.info("Scheduled job started: %s", job_id)
    try:
        async with AsyncSessionLocal() as session:
            result = await cleanup_old_data(session)
            await session.commit()
        logger.info(
            "Scheduled job finished: %s, deleted=%s",
            job_id,
            result,
        )
    except Exception as e:
        logger.exception("Scheduled job failed: %s, error=%s", job_id, e)


def start_scheduler(app: FastAPI | None = None) -> None:
    """Start APScheduler with all configured jobs."""
    global _scheduler
    settings = get_settings()
    _scheduler = AsyncIOScheduler()

    # 1. Market data refresh every N minutes (default 5)
    _scheduler.add_job(
        _job_market_data_refresh,
        "interval",
        minutes=settings.fetch_interval_minutes,
        id="market_data_refresh",
        name="Market data refresh",
    )

    # 2. Analytics computation every N minutes (default 15)
    _scheduler.add_job(
        _job_analytics_computation,
        "interval",
        minutes=settings.analytics_interval_minutes,
        id="analytics_computation",
        name="Analytics computation",
    )

    # 3. Strategy re-evaluation every N minutes (default 60)
    _scheduler.add_job(
        _job_strategy_reevaluation,
        "interval",
        minutes=settings.strategy_interval_minutes,
        id="strategy_reevaluation",
        name="Strategy re-evaluation",
    )

    # 4. Database cleanup every N hours (default 24)
    _scheduler.add_job(
        _job_database_cleanup,
        "interval",
        hours=settings.cleanup_interval_hours,
        id="database_cleanup",
        name="Database cleanup",
    )

    _scheduler.start()
    logger.info(
        "Scheduler started: market_refresh=%sm, analytics=%sm, strategy=%sm, cleanup=%sh",
        settings.fetch_interval_minutes,
        settings.analytics_interval_minutes,
        settings.strategy_interval_minutes,
        settings.cleanup_interval_hours,
    )


def stop_scheduler() -> None:
    """Stop the scheduler."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler stopped")
