"""
SQLAlchemy models for market data.

1. CryptoAsset - Master table for crypto assets
2. MarketData - Time-series price/volume data

Key considerations:
- Composite indexes for time-series query performance (symbol + timestamp)
- DECIMAL for prices/volumes for precision
- Check constraints for data integrity
- Partitioning: For PostgreSQL, market_data can be range-partitioned by timestamp (see docs).
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class CryptoAsset(Base):
    """
    Master table for crypto assets (one row per symbol).
    Used as reference for market data and analytics.
    """

    __tablename__ = "market_assets"  # keep for backward compatibility

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    coingecko_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    market_data: Mapped[list["MarketData"]] = relationship(
        "MarketData",
        back_populates="asset",
        cascade="all, delete-orphan",
    )


class MarketData(Base):
    """
    Time-series price/volume data per asset.
    DECIMAL for precision; composite index (symbol, timestamp) for range queries.
    Partitioning: For large scale, partition by timestamp (e.g. monthly) in PostgreSQL.
    """

    __tablename__ = "price_records"  # keep for backward compatibility

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(
        ForeignKey("market_assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    price: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        nullable=False,
    )
    volume: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(30, 8),
        nullable=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    asset: Mapped["CryptoAsset"] = relationship(
        "CryptoAsset",
        back_populates="market_data",
    )

    __table_args__ = (
        Index("ix_market_data_symbol_timestamp", "symbol", "timestamp"),
        CheckConstraint("price >= 0", name="ck_market_data_price_non_negative"),
        CheckConstraint("volume IS NULL OR volume >= 0", name="ck_market_data_volume_non_negative"),
    )
