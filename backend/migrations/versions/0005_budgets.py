"""budget table

Revision ID: 0005_budgets
Revises: 0004_memory_rules
Create Date: 2026-07-01
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_budgets"
down_revision: str | None = "0004_memory_rules"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "budget",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("user.telegram_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "category_id",
            sa.UUID(),
            sa.ForeignKey("category.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("currency", sa.String(length=5), nullable=False),
        sa.Column("period", sa.String(length=16), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "user_id", "category_id", "period", name="uq_budget_user_cat_period"
        ),
    )
    op.create_index("ix_budget_user_id", "budget", ["user_id"])
    op.create_index("ix_budget_category_id", "budget", ["category_id"])


def downgrade() -> None:
    op.drop_index("ix_budget_category_id", table_name="budget")
    op.drop_index("ix_budget_user_id", table_name="budget")
    op.drop_table("budget")
