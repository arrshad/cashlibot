"""Gamification: streaks, badges, XP + level."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

import sqlalchemy as sa
from sqlalchemy import BigInteger, Column, Date, DateTime, ForeignKey, UniqueConstraint
from sqlmodel import Field, SQLModel

# Streak type strings — kept as bare strings (not an enum) so seeding new
# streak types later is a data change, not a schema/enum migration.
STREAK_DAILY_LOG = "daily_log"
STREAK_BUDGET_ADHERENCE = "budget_adherence"
STREAK_SAVINGS_CONTRIBUTION = "savings_contribution"


def _utcnow() -> datetime:
    return datetime.now(UTC)


class UserStreak(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("user_id", "streak_type", name="uq_userstreak_user_type"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("user.telegram_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    streak_type: str = Field(max_length=32)
    current_count: int = Field(default=0)
    best_count: int = Field(default=0)
    last_activity_date: date | None = Field(
        default=None, sa_column=Column(Date(), nullable=True)
    )


class Badge(SQLModel, table=True):
    """Static catalog of badges. Seeded in migration 0007."""

    id: str = Field(primary_key=True, max_length=64)
    name: str
    name_fa: str | None = Field(default=None)
    description: str
    description_fa: str | None = Field(default=None)
    icon: str = Field(max_length=64)
    xp_reward: int = Field(default=0)


class UserBadge(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("user_id", "badge_id", name="uq_userbadge_user_badge"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("user.telegram_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    badge_id: str = Field(
        sa_column=Column(
            sa.String(length=64),
            ForeignKey("badge.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    earned_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )


class UserXP(SQLModel, table=True):
    user_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("user.telegram_id", ondelete="CASCADE"),
            primary_key=True,
        )
    )
    total_xp: int = Field(default=0)
    level: int = Field(default=1)
    updated_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
