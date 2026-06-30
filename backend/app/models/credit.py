"""Credit ledger — every change to User.credit_balance has a row here."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum

import sqlalchemy as sa
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class CreditReason(str, Enum):
    SIGNUP_BONUS = "signup_bonus"
    REFERRAL_BONUS = "referral_bonus"
    FRIEND_BONUS = "friend_bonus"
    STARS_PURCHASE = "stars_purchase"
    AI_USAGE = "ai_usage"
    ADMIN_ADJUSTMENT = "admin_adjustment"


def _utcnow() -> datetime:
    return datetime.now(UTC)


class CreditTransaction(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("user.telegram_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    change_amount: int                 # positive = credit added, negative = used
    balance_after: int
    reason: CreditReason = Field(
        sa_column=Column(
            SAEnum(
                CreditReason,
                native_enum=False,
                length=32,
                values_callable=lambda cls: [e.value for e in cls],
            ),
            nullable=False,
        ),
    )
    reference_id: str | None = Field(default=None)
    # AI-specific bookkeeping; only set when reason == AI_USAGE.
    ai_tokens_used: int | None = Field(default=None)
    ai_provider: str | None = Field(default=None)
    ai_model: str | None = Field(default=None)
    cost_usd: float | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
