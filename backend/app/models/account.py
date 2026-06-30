"""Account model — checking, cash, card, bank, e-wallet, etc."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum

import sqlalchemy as sa
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class AccountType(str, Enum):
    CASH = "cash"
    CARD = "card"
    BANK = "bank"
    E_WALLET = "e_wallet"
    CREDIT = "credit"
    INVESTMENT = "investment"
    SAVINGS = "savings"


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Account(SQLModel, table=True):
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
    type: AccountType = Field(
        sa_column=Column(
            SAEnum(
                AccountType,
                native_enum=False,
                length=32,
                values_callable=lambda cls: [e.value for e in cls],
            ),
            nullable=False,
        ),
    )
    currency: str
    current_balance: Decimal = Field(
        default=Decimal("0"), max_digits=20, decimal_places=8
    )
    icon: str = Field(default="fa-wallet")
    color: str | None = Field(default=None)
    is_archived: bool = Field(default=False)
    is_default: bool = Field(default=False)
    is_default_income: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
