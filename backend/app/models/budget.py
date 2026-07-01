"""Budget model — per-category spending limits."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum

import sqlalchemy as sa
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class BudgetPeriod(str, Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Budget(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint(
            "user_id", "category_id", "period", name="uq_budget_user_cat_period"
        ),
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
    category_id: uuid.UUID = Field(
        sa_column=Column(
            sa.UUID(),
            ForeignKey("category.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    amount: Decimal = Field(max_digits=20, decimal_places=8)
    currency: str
    period: BudgetPeriod = Field(
        sa_column=Column(
            SAEnum(
                BudgetPeriod,
                native_enum=False,
                length=16,
                values_callable=lambda cls: [e.value for e in cls],
            ),
            nullable=False,
        ),
    )
    is_active: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
