"""Initial tables: market_assets, price_records, strategy_runs, strategy_signals.

Revision ID: 001
Revises:
Create Date: 2025-01-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "market_assets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("coingecko_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_market_assets_coingecko_id"), "market_assets", ["coingecko_id"], unique=False)
    op.create_index(op.f("ix_market_assets_symbol"), "market_assets", ["symbol"], unique=True)

    op.create_table(
        "price_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("price", sa.Numeric(20, 8), nullable=False),
        sa.Column("volume", sa.Numeric(30, 8), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["asset_id"], ["market_assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_price_records_asset_id"), "price_records", ["asset_id"], unique=False)
    op.create_index(op.f("ix_price_records_symbol"), "price_records", ["symbol"], unique=False)
    op.create_index(op.f("ix_price_records_timestamp"), "price_records", ["timestamp"], unique=False)

    op.create_table(
        "strategy_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("strategy_name", sa.String(100), nullable=False),
        sa.Column("params_snapshot", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "strategy_signals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("signal", sa.String(10), nullable=False),
        sa.Column("price_at_signal", sa.String(50), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["strategy_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_strategy_signals_run_id"), "strategy_signals", ["run_id"], unique=False)
    op.create_index(op.f("ix_strategy_signals_symbol"), "strategy_signals", ["symbol"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_strategy_signals_symbol"), table_name="strategy_signals")
    op.drop_index(op.f("ix_strategy_signals_run_id"), table_name="strategy_signals")
    op.drop_table("strategy_signals")
    op.drop_table("strategy_runs")
    op.drop_index(op.f("ix_price_records_timestamp"), table_name="price_records")
    op.drop_index(op.f("ix_price_records_symbol"), table_name="price_records")
    op.drop_index(op.f("ix_price_records_asset_id"), table_name="price_records")
    op.drop_table("price_records")
    op.drop_index(op.f("ix_market_assets_symbol"), table_name="market_assets")
    op.drop_index(op.f("ix_market_assets_coingecko_id"), table_name="market_assets")
    op.drop_table("market_assets")
