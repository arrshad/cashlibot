"""Account model — checking, cash, card, bank, e-wallet, etc."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import BigInteger, Column, ForeignKey
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
    type: AccountType
    currency: str
    current_balance: Decimal = Field(
        default=Decimal("0"), max_digits=20, decimal_places=8
    )
    icon: str = Field(default="fa-wallet")
    color: str | None = Field(default=None)
    is_archived: bool = Field(default=False)
    is_default: bool = Field(default=False)
    is_default_income: bool = Field(default=False)
    created_at: datetime = Field(default_factory=_utcnow)
