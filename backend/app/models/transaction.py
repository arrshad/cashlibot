"""Transaction ledger — every income / expense / transfer lives here."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum

import sqlalchemy as sa
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"


class TransactionSource(str, Enum):
    MANUAL = "manual"
    AI_PARSED = "ai_parsed"
    RECURRING = "recurring"


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _tz_dt(nullable: bool = False, server_default: bool = True) -> Column:
    return Column(
        DateTime(timezone=True),
        nullable=nullable,
        server_default=sa.func.now() if server_default else None,
    )


class Transaction(SQLModel, table=True):
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
            index=True,
        )
    )
    category_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            sa.UUID(),
            ForeignKey("category.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    type: TransactionType = Field(
        sa_column=Column(
            SAEnum(
                TransactionType,
                native_enum=False,
                length=16,
                values_callable=lambda cls: [e.value for e in cls],
            ),
            nullable=False,
        ),
    )
    amount: Decimal = Field(max_digits=20, decimal_places=8)
    currency: str
    merchant: str | None = Field(default=None)
    description: str | None = Field(default=None)
    occurred_at: datetime = Field(sa_column=_tz_dt(server_default=False))
    to_account_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            sa.UUID(),
            ForeignKey("account.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    source: TransactionSource = Field(
        default=TransactionSource.MANUAL,
        sa_column=Column(
            SAEnum(
                TransactionSource,
                native_enum=False,
                length=16,
                values_callable=lambda cls: [e.value for e in cls],
            ),
            nullable=False,
            server_default=TransactionSource.MANUAL.value,
        ),
    )
    raw_input_text: str | None = Field(default=None)
    reply_to_message_id: int | None = Field(default=None)
    ai_confidence: float | None = Field(default=None)
    is_deleted: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=_utcnow, sa_column=_tz_dt())
    updated_at: datetime = Field(default_factory=_utcnow, sa_column=_tz_dt())
