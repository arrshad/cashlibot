"""sharedexpense + sharedexpensesplit tables

Revision ID: 0013_shared_expenses
Revises: 0012_friend_badge
Create Date: 2026-07-02
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013_shared_expenses"
down_revision: str | None = "0012_friend_badge"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sharedexpense",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "created_by_user_id",
            sa.BigInteger(),
            sa.ForeignKey("user.telegram_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("total_amount", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("currency", sa.String(length=5), nullable=False),
        sa.Column(
            "related_transaction_id",
            sa.UUID(),
            sa.ForeignKey("transaction.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "status", sa.String(length=32), nullable=False, server_default="open"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_sharedexpense_created_by_user_id",
        "sharedexpense",
        ["created_by_user_id"],
    )

    op.create_table(
        "sharedexpensesplit",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "shared_expense_id",
            sa.UUID(),
            sa.ForeignKey("sharedexpense.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("user.telegram_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount_owed", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="pending_approval",
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "settlement_transaction_id",
            sa.UUID(),
            sa.ForeignKey("transaction.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "shared_expense_id",
            "user_id",
            name="uq_sharedexpensesplit_expense_user",
        ),
    )
    op.create_index(
        "ix_sharedexpensesplit_shared_expense_id",
        "sharedexpensesplit",
        ["shared_expense_id"],
    )
    op.create_index(
        "ix_sharedexpensesplit_user_id", "sharedexpensesplit", ["user_id"]
    )
    op.create_index(
        "ix_sharedexpensesplit_status", "sharedexpensesplit", ["status"]
    )


def downgrade() -> None:
    op.drop_index(
        "ix_sharedexpensesplit_status", table_name="sharedexpensesplit"
    )
    op.drop_index(
        "ix_sharedexpensesplit_user_id", table_name="sharedexpensesplit"
    )
    op.drop_index(
        "ix_sharedexpensesplit_shared_expense_id",
        table_name="sharedexpensesplit",
    )
    op.drop_table("sharedexpensesplit")
    op.drop_index(
        "ix_sharedexpense_created_by_user_id", table_name="sharedexpense"
    )
    op.drop_table("sharedexpense")
