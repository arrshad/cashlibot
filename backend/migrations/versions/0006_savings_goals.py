"""savingsgoal table

Revision ID: 0006_savings
Revises: 0005_budgets
Create Date: 2026-07-01
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_savings"
down_revision: str | None = "0005_budgets"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "savingsgoal",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("user.telegram_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("icon", sa.String(), nullable=False, server_default="fa-piggy-bank"),
        sa.Column(
            "target_amount", sa.Numeric(precision=20, scale=8), nullable=False
        ),
        sa.Column(
            "current_amount",
            sa.Numeric(precision=20, scale=8),
            nullable=False,
            server_default="0",
        ),
        sa.Column("currency", sa.String(length=5), nullable=False),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column(
            "linked_account_id",
            sa.UUID(),
            sa.ForeignKey("account.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "is_completed", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_savingsgoal_user_id", "savingsgoal", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_savingsgoal_user_id", table_name="savingsgoal")
    op.drop_table("savingsgoal")
