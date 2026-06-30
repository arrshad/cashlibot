"""Category model — for transaction classification."""

from __future__ import annotations

import uuid
from enum import Enum

from sqlalchemy import BigInteger, Column, ForeignKey
from sqlmodel import Field, SQLModel


class CategoryType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class Category(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    # null = system-wide default category. Currently every user gets their own
    # copy seeded at onboarding, but the column stays nullable so we can switch
    # to (or mix in) global defaults later without a schema change.
    user_id: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger,
            ForeignKey("user.telegram_id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
    )
    name: str                         # what the user sees in their locale
    name_en: str                      # canonical English name (used by the AI for matching)
    name_fa: str | None = Field(default=None)
    type: CategoryType
    parent_id: uuid.UUID | None = Field(
        default=None, foreign_key="category.id"
    )
    icon: str = Field(default="fa-tag")
    color: str | None = Field(default=None)
    is_archived: bool = Field(default=False)
