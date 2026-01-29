"""AnalyticsResult table, composite indexes, and check constraints.

Revision ID: 002
Revises: 001
Create Date: 2025-01-29

- analytics_results: computed analytics per symbol/window
- price_records: composite index (symbol, timestamp), check price > 0, volume >= 0
- strategy_signals: composite index (run_id, symbol), check signal IN (BUY, SELL, HOLD)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Composite index for time-series queries on price_records
    op.create_index(
        "ix_market_data_symbol_timestamp",
        "price_records",
        ["symbol", "timestamp"],
        unique=False,
    )
    op.create_check_constraint(
        "ck_market_data_price_non_negative",
        "price_records",
        "price >= 0",
    )
    op.create_check_constraint(
        "ck_market_data_volume_non_negative",
        "price_records",
        "volume IS NULL OR volume >= 0",
    )

    # analytics_results table
    op.create_table(
        "analytics_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("window_hours", sa.Integer(), nullable=False),
        sa.Column("price_change_pct", sa.Float(), nullable=True),
        sa.Column("volume_change_pct", sa.Float(), nullable=True),
        sa.Column("momentum", sa.Float(), nullable=True),
        sa.Column("current_price", sa.Numeric(20, 8), nullable=True),
        sa.Column("current_volume", sa.Numeric(30, 8), nullable=True),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_analytics_results_symbol"),
        "analytics_results",
        ["symbol"],
        unique=False,
    )
    op.create_index(
        op.f("ix_analytics_results_window_hours"),
        "analytics_results",
        ["window_hours"],
        unique=False,
    )
    op.create_index(
        op.f("ix_analytics_results_computed_at"),
        "analytics_results",
        ["computed_at"],
        unique=False,
    )
    op.create_index(
        "ix_analytics_results_symbol_window_computed",
        "analytics_results",
        ["symbol", "window_hours", "computed_at"],
        unique=False,
    )

    # Composite index and check constraint on strategy_signals
    op.create_index(
        "ix_strategy_signals_run_symbol",
        "strategy_signals",
        ["run_id", "symbol"],
        unique=False,
    )
    op.create_check_constraint(
        "ck_strategy_signal_valid",
        "strategy_signals",
        "signal IN ('BUY', 'SELL', 'HOLD')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_strategy_signal_valid", "strategy_signals", type_="check")
    op.drop_index("ix_strategy_signals_run_symbol", table_name="strategy_signals")

    op.drop_index("ix_analytics_results_symbol_window_computed", table_name="analytics_results")
    op.drop_index(op.f("ix_analytics_results_computed_at"), table_name="analytics_results")
    op.drop_index(op.f("ix_analytics_results_window_hours"), table_name="analytics_results")
    op.drop_index(op.f("ix_analytics_results_symbol"), table_name="analytics_results")
    op.drop_table("analytics_results")

    op.drop_constraint("ck_market_data_volume_non_negative", "price_records", type_="check")
    op.drop_constraint("ck_market_data_price_non_negative", "price_records", type_="check")
    op.drop_index("ix_market_data_symbol_timestamp", table_name="price_records")
