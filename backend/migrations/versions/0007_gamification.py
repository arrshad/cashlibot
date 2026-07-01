"""streaks + badges + user_xp (with badge catalog seed)

Revision ID: 0007_gamification
Revises: 0006_savings
Create Date: 2026-07-01
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_gamification"
down_revision: str | None = "0006_savings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# id → (name_en, name_fa, description_en, description_fa, icon, xp_reward)
BADGES: tuple[tuple[str, str, str, str, str, str, int], ...] = (
    ("first_transaction", "First Step", "اولین قدم",
     "You logged your first transaction.",
     "اولین تراکنشت رو ثبت کردی.",
     "fa-shoe-prints", 20),
    ("week_streak", "Week Warrior", "قهرمان هفته",
     "Seven days in a row of logging.",
     "هفت روز پشت سر هم ثبت کردی.",
     "fa-fire", 50),
    ("month_streak", "Monthly Master", "استاد ماه",
     "Thirty-day logging streak.",
     "سی روز پشت سر هم ثبت کردی.",
     "fa-award", 200),
    ("saver", "Saver", "پس‌اندازگر",
     "First contribution to a savings goal.",
     "اولین کمک به هدف پس‌اندازت.",
     "fa-piggy-bank", 30),
    ("goal_reached", "Goal Crusher", "هدف‌شکن",
     "You completed a savings goal.",
     "یه هدف پس‌انداز رو تکمیل کردی.",
     "fa-trophy", 100),
    ("ai_user", "Early Adopter", "پیشرو",
     "First transaction logged via the AI.",
     "اولین تراکنش با هوش مصنوعی.",
     "fa-wand-magic-sparkles", 25),
    ("power_user", "Power User", "کاربر حرفه‌ای",
     "One hundred transactions logged.",
     "صد تراکنش ثبت کردی.",
     "fa-bolt", 100),
)


def upgrade() -> None:
    op.create_table(
        "userstreak",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("user.telegram_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("streak_type", sa.String(length=32), nullable=False),
        sa.Column("current_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("best_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_activity_date", sa.Date(), nullable=True),
        sa.UniqueConstraint("user_id", "streak_type", name="uq_userstreak_user_type"),
    )
    op.create_index("ix_userstreak_user_id", "userstreak", ["user_id"])

    op.create_table(
        "badge",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("name_fa", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("description_fa", sa.Text(), nullable=True),
        sa.Column("icon", sa.String(length=64), nullable=False),
        sa.Column("xp_reward", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "userbadge",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("user.telegram_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "badge_id",
            sa.String(length=64),
            sa.ForeignKey("badge.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "earned_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("user_id", "badge_id", name="uq_userbadge_user_badge"),
    )
    op.create_index("ix_userbadge_user_id", "userbadge", ["user_id"])
    op.create_index("ix_userbadge_badge_id", "userbadge", ["badge_id"])

    op.create_table(
        "userxp",
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("user.telegram_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("total_xp", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Seed the badge catalog. Using op.bulk_insert avoids hand-rolled SQL.
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
    op.bulk_insert(
        badge_table,
        [
            {
                "id": bid,
                "name": name_en,
                "name_fa": name_fa,
                "description": desc_en,
                "description_fa": desc_fa,
                "icon": icon,
                "xp_reward": xp,
            }
            for (bid, name_en, name_fa, desc_en, desc_fa, icon, xp) in BADGES
        ],
    )


def downgrade() -> None:
    op.drop_table("userxp")
    op.drop_index("ix_userbadge_badge_id", table_name="userbadge")
    op.drop_index("ix_userbadge_user_id", table_name="userbadge")
    op.drop_table("userbadge")
    op.drop_table("badge")
    op.drop_index("ix_userstreak_user_id", table_name="userstreak")
    op.drop_table("userstreak")
