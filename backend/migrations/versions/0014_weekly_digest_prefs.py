"""weekly digest preferences on user

Revision ID: 0014_weekly_digest
Revises: 0013_shared_expenses
Create Date: 2026-07-02
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014_weekly_digest"
down_revision: str | None = "0013_shared_expenses"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "user",
        sa.Column(
            "weekly_digest_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.add_column(
        "user",
        sa.Column(
            "weekly_digest_hour",
            sa.Integer(),
            nullable=False,
            server_default="9",
        ),
    )
    # 0=Monday .. 6=Sunday, matching Python's datetime.weekday().
    op.add_column(
        "user",
        sa.Column(
            "weekly_digest_dow",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "user",
        sa.Column(
            "last_weekly_digest_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("user", "last_weekly_digest_at")
    op.drop_column("user", "weekly_digest_dow")
    op.drop_column("user", "weekly_digest_hour")
    op.drop_column("user", "weekly_digest_enabled")
