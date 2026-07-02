"""friendship table

Revision ID: 0011_friendships
Revises: 0010_recurring
Create Date: 2026-07-02
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011_friendships"
down_revision: str | None = "0010_recurring"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "friendship",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "requester_id",
            sa.BigInteger(),
            sa.ForeignKey("user.telegram_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "addressee_id",
            sa.BigInteger(),
            sa.ForeignKey("user.telegram_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
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
        sa.CheckConstraint(
            "requester_id != addressee_id", name="ck_friendship_no_self"
        ),
    )
    op.create_index("ix_friendship_requester_id", "friendship", ["requester_id"])
    op.create_index("ix_friendship_addressee_id", "friendship", ["addressee_id"])

    # Prevent duplicate friendships between the same two users regardless of
    # who requested first. Using LEAST/GREATEST here so a pending A→B blocks
    # a follow-up B→A.
    op.execute(
        """
        CREATE UNIQUE INDEX uq_friendship_pair
        ON friendship (
            LEAST(requester_id, addressee_id),
            GREATEST(requester_id, addressee_id)
        )
        WHERE status IN ('pending', 'accepted')
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_friendship_pair")
    op.drop_index("ix_friendship_addressee_id", table_name="friendship")
    op.drop_index("ix_friendship_requester_id", table_name="friendship")
    op.drop_table("friendship")
