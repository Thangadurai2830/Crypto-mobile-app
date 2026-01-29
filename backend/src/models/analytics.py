"""
SQLAlchemy model for computed analytics.

AnalyticsResult - Stores computed analytics (price/volume change %, momentum)
per symbol and window. Composite index (symbol, window_hours, computed_at) for lookups.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class AnalyticsResult(Base):
    """
    Computed analytics per symbol and time window.
    One row per (symbol, window_hours, computed_at) snapshot.
    """

    __tablename__ = "analytics_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    window_hours: Mapped[int] = mapped_column(nullable=False, index=True)
    price_change_pct: Mapped[Optional[float]] = mapped_column(nullable=True)
    volume_change_pct: Mapped[Optional[float]] = mapped_column(nullable=True)
    momentum: Mapped[Optional[float]] = mapped_column(nullable=True)
    current_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 8),
        nullable=True,
    )
    current_volume: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(30, 8),
        nullable=True,
    )
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        server_default=func.now(),
    )

    __table_args__ = (
        # Composite index for "latest analytics per symbol/window"
        Index(
            "ix_analytics_results_symbol_window_computed",
            "symbol",
            "window_hours",
            "computed_at",
        ),
    )
