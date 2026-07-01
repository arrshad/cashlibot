"""Savings goal model — track progress toward a target."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy import BigInteger, Column, Date, DateTime, ForeignKey
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(UTC)


class SavingsGoal(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("user.telegram_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    name: str
    icon: str = Field(default="fa-piggy-bank")
    target_amount: Decimal = Field(max_digits=20, decimal_places=8)
    current_amount: Decimal = Field(
        default=Decimal("0"), max_digits=20, decimal_places=8
    )
    currency: str
    deadline: date | None = Field(
        default=None, sa_column=Column(Date(), nullable=True)
    )
    linked_account_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            sa.UUID(),
            ForeignKey("account.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    is_completed: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
