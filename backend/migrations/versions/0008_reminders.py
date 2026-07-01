"""reminder table

Revision ID: 0008_reminders
Revises: 0007_gamification
Create Date: 2026-07-01
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_reminders"
down_revision: str | None = "0007_gamification"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reminder",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("user.telegram_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("reminder_type", sa.String(length=32), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("repeat_frequency", sa.String(length=16), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column("last_fired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("related_friend_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "related_amount", sa.Numeric(precision=20, scale=8), nullable=True
        ),
        sa.Column("related_currency", sa.String(length=5), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_reminder_user_id", "reminder", ["user_id"])
    op.create_index("ix_reminder_due_at", "reminder", ["due_at"])
    op.create_index("ix_reminder_is_active", "reminder", ["is_active"])
    # Tick query filters on (is_active, due_at). Compound index speeds it up.
    op.create_index(
        "ix_reminder_active_due", "reminder", ["is_active", "due_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_reminder_active_due", table_name="reminder")
    op.drop_index("ix_reminder_is_active", table_name="reminder")
    op.drop_index("ix_reminder_due_at", table_name="reminder")
    op.drop_index("ix_reminder_user_id", table_name="reminder")
    op.drop_table("reminder")
