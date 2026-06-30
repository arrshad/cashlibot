"""initial schema: pgvector extension + user table

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-30
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel  # noqa: F401  (used by autogenerate in later migrations)
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # pgvector lives in this DB; subsequent migrations can add Vector columns.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "user",
        sa.Column("telegram_id", sa.BigInteger(), primary_key=True, nullable=False),
        sa.Column("username", sa.String(), nullable=True),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("language_code", sa.String(), nullable=False, server_default="en"),
        sa.Column("timezone", sa.String(), nullable=False, server_default="UTC"),
        sa.Column("calendar_system", sa.String(), nullable=False, server_default="gregorian"),
        sa.Column("default_currency", sa.String(), nullable=True),
        sa.Column("credit_balance", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "onboarding_completed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_user_username", "user", ["username"])


def downgrade() -> None:
    op.drop_index("ix_user_username", table_name="user")
    op.drop_table("user")
    op.execute("DROP EXTENSION IF EXISTS vector")
