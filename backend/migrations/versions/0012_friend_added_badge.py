"""seed friend_added badge

Revision ID: 0012_friend_badge
Revises: 0011_friendships
Create Date: 2026-07-02

Migration 0007 seeded seven badges but missed friend_added, which the
friends flow awards on the first accepted friendship. Adding it here as
data-only.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012_friend_badge"
down_revision: str | None = "0011_friendships"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


BADGE = {
    "id": "friend_added",
    "name": "Social",
    "name_fa": "اجتماعی",
    "description": "First accepted friendship on Cashlibot.",
    "description_fa": "اولین دوستی تأیید شده تو Cashlibot.",
    "icon": "fa-user-plus",
    "xp_reward": 20,
}


def upgrade() -> None:
    badge_table = sa.table(
        "badge",
        sa.column("id", sa.String()),
        sa.column("name", sa.String()),
        sa.column("name_fa", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("description_fa", sa.Text()),
        sa.column("icon", sa.String()),
        sa.column("xp_reward", sa.Integer()),
    )
    op.bulk_insert(badge_table, [BADGE])


def downgrade() -> None:
    op.execute(f"DELETE FROM badge WHERE id = '{BADGE['id']}'")
