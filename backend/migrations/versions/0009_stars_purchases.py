"""starspurchase table

Revision ID: 0009_stars
Revises: 0008_reminders
Create Date: 2026-07-02
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_stars"
down_revision: str | None = "0008_reminders"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "starspurchase",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("user.telegram_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("telegram_charge_id", sa.String(), nullable=False, unique=True),
        sa.Column("stars_amount", sa.Integer(), nullable=False),
        sa.Column("credits_granted", sa.Integer(), nullable=False),
        sa.Column("package_id", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_starspurchase_user_id", "starspurchase", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_starspurchase_user_id", table_name="starspurchase")
    op.drop_table("starspurchase")
