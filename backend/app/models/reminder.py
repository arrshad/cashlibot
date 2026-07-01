"""Reminder model — one-shot or repeating chat nudges."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum

import sqlalchemy as sa
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

from app.models.frequency import Frequency


class ReminderType(str, Enum):
    TRANSACTION_LOG = "transaction_log"
    PAY_SOMEONE = "pay_someone"
    BILL_DUE = "bill_due"
    MONTHLY_REVIEW = "monthly_review"
    CUSTOM = "custom"


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Reminder(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("user.telegram_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    title: str = Field(max_length=200)
    description: str | None = Field(default=None)
    reminder_type: ReminderType = Field(
        sa_column=Column(
            SAEnum(
                ReminderType,
                native_enum=False,
                length=32,
                values_callable=lambda cls: [e.value for e in cls],
            ),
            nullable=False,
        ),
    )
    due_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True)
    )
    repeat_frequency: Frequency | None = Field(
        default=None,
        sa_column=Column(
            SAEnum(
                Frequency,
                native_enum=False,
                length=16,
                values_callable=lambda cls: [e.value for e in cls],
            ),
            nullable=True,
        ),
    )
    is_active: bool = Field(default=True, index=True)
    last_fired_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    # Stubs for friends-linked reminders like "pay Ali 50 EUR". Populated
    # once the friends feature lands.
    related_friend_id: int | None = Field(default=None)
    related_amount: Decimal | None = Field(
        default=None, max_digits=20, decimal_places=8
    )
    related_currency: str | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
