"""Payment ledger for Telegram Stars purchases."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(UTC)


class StarsPurchase(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("user.telegram_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    # Telegram guarantees a unique charge id per SuccessfulPayment. We rely on
    # the UNIQUE constraint to make credit grants idempotent.
    telegram_charge_id: str = Field(sa_column=Column(sa.String(), unique=True, nullable=False))
    stars_amount: int
    credits_granted: int
    package_id: str = Field(max_length=64)
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
