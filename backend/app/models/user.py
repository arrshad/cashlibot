"""User table model."""

from __future__ import annotations

from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy import BigInteger, Column, DateTime
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _tz_dt_column() -> Column:
    return Column(
        DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )


class User(SQLModel, table=True):
    # Telegram user IDs can exceed 32 bits — pin the column to BigInteger.
    telegram_id: int = Field(
        sa_column=Column(BigInteger, primary_key=True, autoincrement=False)
    )
    username: str | None = Field(default=None, index=True)
    display_name: str
    language_code: str = Field(default="en")          # "en" | "fa"
    timezone: str = Field(default="UTC")              # IANA TZ name
    calendar_system: str = Field(default="gregorian") # "gregorian" | "jalali" | "hijri"
    default_currency: str | None = Field(default=None)
    credit_balance: int = Field(default=0)
    is_admin: bool = Field(default=False)
    onboarding_completed: bool = Field(default=False)

    # Weekly digest DM prefs (opt-out). Hour is 0-23 in the user's timezone,
    # dow is 0=Mon..6=Sun (matches datetime.weekday()).
    weekly_digest_enabled: bool = Field(default=True)
    weekly_digest_hour: int = Field(default=9)
    weekly_digest_dow: int = Field(default=0)
    last_weekly_digest_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    created_at: datetime = Field(default_factory=_utcnow, sa_column=_tz_dt_column())
    updated_at: datetime = Field(default_factory=_utcnow, sa_column=_tz_dt_column())
