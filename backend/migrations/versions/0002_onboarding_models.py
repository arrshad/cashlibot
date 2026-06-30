"""accounts, categories, credit transactions

Revision ID: 0002_onboarding
Revises: 0001_initial
Create Date: 2026-06-30
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_onboarding"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "account",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("user.telegram_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("currency", sa.String(length=5), nullable=False),
        sa.Column(
            "current_balance",
            sa.Numeric(precision=20, scale=8),
            nullable=False,
            server_default="0",
        ),
        sa.Column("icon", sa.String(), nullable=False, server_default="fa-wallet"),
        sa.Column("color", sa.String(), nullable=True),
        sa.Column(
            "is_archived", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "is_default", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "is_default_income",
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
    )
    op.create_index("ix_account_user_id", "account", ["user_id"])

    op.create_table(
        "category",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("user.telegram_id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("name_en", sa.String(), nullable=False),
        sa.Column("name_fa", sa.String(), nullable=True),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.Column(
            "parent_id",
            sa.UUID(),
            sa.ForeignKey("category.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("icon", sa.String(), nullable=False, server_default="fa-tag"),
        sa.Column("color", sa.String(), nullable=True),
        sa.Column(
            "is_archived", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.create_index("ix_category_user_id", "category", ["user_id"])

    op.create_table(
        "credittransaction",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("user.telegram_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("change_amount", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=32), nullable=False),
        sa.Column("reference_id", sa.String(), nullable=True),
        sa.Column("ai_tokens_used", sa.Integer(), nullable=True),
        sa.Column("ai_provider", sa.String(), nullable=True),
        sa.Column("ai_model", sa.String(), nullable=True),
        sa.Column("cost_usd", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_credittransaction_user_id", "credittransaction", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_credittransaction_user_id", table_name="credittransaction")
    op.drop_table("credittransaction")
    op.drop_index("ix_category_user_id", table_name="category")
    op.drop_table("category")
    op.drop_index("ix_account_user_id", table_name="account")
    op.drop_table("account")
