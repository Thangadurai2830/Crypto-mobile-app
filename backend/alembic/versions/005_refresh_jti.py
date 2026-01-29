"""Add refresh_jti to sessions for JWT refresh token rotation.

Revision ID: 005
Revises: 004
Create Date: 2025-01-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sessions",
        sa.Column("refresh_jti", sa.String(64), nullable=True),
    )
    op.create_index(op.f("ix_sessions_refresh_jti"), "sessions", ["refresh_jti"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_sessions_refresh_jti"), table_name="sessions")
    op.drop_column("sessions", "refresh_jti")
