"""Semantic user memory backed by pgvector."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

EMBEDDING_DIM = 1536


class MemoryType(str, Enum):
    PREFERENCE = "preference"
    ACCOUNT_DEFAULT = "account_default"
    CATEGORY_HABIT = "category_habit"
    CONTACT = "contact"
    CONTEXT = "context"


def _utcnow() -> datetime:
    return datetime.now(UTC)


class UserMemory(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("user.telegram_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    memory_type: MemoryType = Field(
        sa_column=Column(
            SAEnum(
                MemoryType,
                native_enum=False,
                length=32,
                values_callable=lambda cls: [e.value for e in cls],
            ),
            nullable=False,
        ),
    )
    content: str
    embedding: list[float] = Field(sa_column=Column(Vector(EMBEDDING_DIM), nullable=False))
    metadata_json: str | None = Field(default=None)
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
