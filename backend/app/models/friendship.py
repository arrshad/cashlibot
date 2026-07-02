"""Friendship model — mutual bond between two users."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum

import sqlalchemy as sa
from sqlalchemy import BigInteger, CheckConstraint, Column, DateTime, ForeignKey
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class FriendshipStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Friendship(SQLModel, table=True):
    __table_args__ = (
        CheckConstraint(
            "requester_id != addressee_id",
            name="ck_friendship_no_self",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    requester_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("user.telegram_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    addressee_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("user.telegram_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    status: FriendshipStatus = Field(
        default=FriendshipStatus.PENDING,
        sa_column=Column(
            SAEnum(
                FriendshipStatus,
                native_enum=False,
                length=16,
                values_callable=lambda cls: [e.value for e in cls],
            ),
            nullable=False,
            server_default=FriendshipStatus.PENDING.value,
        ),
    )
    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    updated_at: datetime = Field(
        default_factory=_utcnow,
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
