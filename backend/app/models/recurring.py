"""Recurring transaction templates + their occurrences."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum

import sqlalchemy as sa
from sqlalchemy import BigInteger, Column, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

from app.models.frequency import Frequency


class OccurrenceStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SKIPPED = "skipped"


def _utcnow() -> datetime:
    return datetime.now(UTC)


class RecurringTemplate(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("user.telegram_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    account_id: uuid.UUID = Field(
        sa_column=Column(
            sa.UUID(),
            ForeignKey("account.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    category_id: uuid.UUID = Field(
        sa_column=Column(
            sa.UUID(),
            ForeignKey("category.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    amount: Decimal = Field(max_digits=20, decimal_places=8)
    currency: str
    description: str
    frequency: Frequency = Field(
        sa_column=Column(
            SAEnum(
                Frequency,
                native_enum=False,
                length=16,
                values_callable=lambda cls: [e.value for e in cls],
            ),
            nullable=False,
        ),
    )
    next_due_date: date = Field(
        sa_column=Column(Date(), nullable=False, index=True)
    )
    is_active: bool = Field(default=True, index=True)
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )


class RecurringOccurrence(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint(
            "template_id", "due_date", name="uq_recurringoccurrence_template_due"
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    template_id: uuid.UUID = Field(
        sa_column=Column(
            sa.UUID(),
            ForeignKey("recurringtemplate.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    due_date: date = Field(sa_column=Column(Date(), nullable=False, index=True))
    status: OccurrenceStatus = Field(
        default=OccurrenceStatus.PENDING,
        sa_column=Column(
            SAEnum(
                OccurrenceStatus,
                native_enum=False,
                length=16,
                values_callable=lambda cls: [e.value for e in cls],
            ),
            nullable=False,
            server_default=OccurrenceStatus.PENDING.value,
        ),
    )
    confirmed_transaction_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            sa.UUID(),
            ForeignKey("transaction.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
