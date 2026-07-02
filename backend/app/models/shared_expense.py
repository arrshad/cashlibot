"""Shared expenses split across friends."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum

import sqlalchemy as sa
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class SharedExpenseStatus(str, Enum):
    OPEN = "open"
    PARTIALLY_SETTLED = "partially_settled"
    FULLY_SETTLED = "fully_settled"


class SplitStatus(str, Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    DISPUTED = "disputed"
    SETTLED = "settled"


def _utcnow() -> datetime:
    return datetime.now(UTC)


class SharedExpense(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_by_user_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("user.telegram_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    description: str
    total_amount: Decimal = Field(max_digits=20, decimal_places=8)
    currency: str
    related_transaction_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            sa.UUID(),
            ForeignKey("transaction.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    status: SharedExpenseStatus = Field(
        default=SharedExpenseStatus.OPEN,
        sa_column=Column(
            SAEnum(
                SharedExpenseStatus,
                native_enum=False,
                length=32,
                values_callable=lambda cls: [e.value for e in cls],
            ),
            nullable=False,
            server_default=SharedExpenseStatus.OPEN.value,
        ),
    )
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )


class SharedExpenseSplit(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint(
            "shared_expense_id",
            "user_id",
            name="uq_sharedexpensesplit_expense_user",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    shared_expense_id: uuid.UUID = Field(
        sa_column=Column(
            sa.UUID(),
            ForeignKey("sharedexpense.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    user_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("user.telegram_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    amount_owed: Decimal = Field(max_digits=20, decimal_places=8)
    status: SplitStatus = Field(
        default=SplitStatus.PENDING_APPROVAL,
        sa_column=Column(
            SAEnum(
                SplitStatus,
                native_enum=False,
                length=32,
                values_callable=lambda cls: [e.value for e in cls],
            ),
            nullable=False,
            server_default=SplitStatus.PENDING_APPROVAL.value,
            index=True,
        ),
    )
    approved_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    settled_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    settlement_transaction_id: uuid.UUID | None = Field(
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
