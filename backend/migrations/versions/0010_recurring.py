"""recurringtemplate + recurringoccurrence

Revision ID: 0010_recurring
Revises: 0009_stars
Create Date: 2026-07-02
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010_recurring"
down_revision: str | None = "0009_stars"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "recurringtemplate",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("user.telegram_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "account_id",
            sa.UUID(),
            sa.ForeignKey("account.id", ondelete="CASCADE"),
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
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("frequency", sa.String(length=16), nullable=False),
        sa.Column("next_due_date", sa.Date(), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_recurringtemplate_user_id", "recurringtemplate", ["user_id"])
    op.create_index(
        "ix_recurringtemplate_next_due_date", "recurringtemplate", ["next_due_date"]
    )
    op.create_index(
        "ix_recurringtemplate_is_active", "recurringtemplate", ["is_active"]
    )

    op.create_table(
        "recurringoccurrence",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "template_id",
            sa.UUID(),
            sa.ForeignKey("recurringtemplate.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "confirmed_transaction_id",
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
            "template_id", "due_date", name="uq_recurringoccurrence_template_due"
        ),
    )
    op.create_index(
        "ix_recurringoccurrence_template_id",
        "recurringoccurrence",
        ["template_id"],
    )
    op.create_index(
        "ix_recurringoccurrence_due_date", "recurringoccurrence", ["due_date"]
    )


def downgrade() -> None:
    op.drop_index(
        "ix_recurringoccurrence_due_date", table_name="recurringoccurrence"
    )
    op.drop_index(
        "ix_recurringoccurrence_template_id", table_name="recurringoccurrence"
    )
    op.drop_table("recurringoccurrence")
    op.drop_index(
        "ix_recurringtemplate_is_active", table_name="recurringtemplate"
    )
    op.drop_index(
        "ix_recurringtemplate_next_due_date", table_name="recurringtemplate"
    )
    op.drop_index("ix_recurringtemplate_user_id", table_name="recurringtemplate")
    op.drop_table("recurringtemplate")
