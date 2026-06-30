"""User table model."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import BigInteger, Column
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(UTC)


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
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
