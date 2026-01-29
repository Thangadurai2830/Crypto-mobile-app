"""
Strategy run and signal models.

StrategySignal - Generated trading signals (BUY/SELL/HOLD) per asset per run.
Check constraint for signal enum; composite index (run_id, symbol) for lookups.
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class StrategyRun(Base):
    """One execution of the strategy (e.g. MA crossover)."""

    __tablename__ = "strategy_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    strategy_name: Mapped[str] = mapped_column(String(100), nullable=False)
    params_snapshot: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    status: Mapped[str] = mapped_column(String(20), default="completed")

    signals: Mapped[list["StrategySignal"]] = relationship(
        "StrategySignal",
        back_populates="run",
        cascade="all, delete-orphan",
    )


class StrategySignal(Base):
    """Per-asset signal from a strategy run. Constraint: signal IN (BUY, SELL, HOLD)."""

    __tablename__ = "strategy_signals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("strategy_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    signal: Mapped[str] = mapped_column(String(10), nullable=False)
    price_at_signal: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    run: Mapped["StrategyRun"] = relationship("StrategyRun", back_populates="signals")

    __table_args__ = (
        Index("ix_strategy_signals_run_symbol", "run_id", "symbol"),
        CheckConstraint(
            "signal IN ('BUY', 'SELL', 'HOLD')",
            name="ck_strategy_signal_valid",
        ),
    )
