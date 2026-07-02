"""User data export.

Two shapes:

- `build_json_dump(...)` — everything the user has in one JSON document.
  Amounts are strings so decimal precision survives the JSON round-trip.
- `build_transactions_csv(...)` — transactions only, spreadsheet-ready.

Neither shape leaks server-side flags (bot token, is_admin, JWT bits).
"""

from __future__ import annotations

import csv
import io
import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.budget import Budget
from app.models.category import Category
from app.models.credit import CreditTransaction
from app.models.savings_goal import SavingsGoal
from app.models.transaction import Transaction
from app.models.user import User

EXPORT_SCHEMA_VERSION = 1


def _json_default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    raise TypeError(f"unsupported type: {type(value).__name__}")


def _row(obj: Any, fields: list[str]) -> dict[str, Any]:
    return {field: getattr(obj, field, None) for field in fields}


async def build_json_dump(
    session: AsyncSession, *, user: User
) -> dict[str, Any]:
    """Assemble the full user-owned dataset as a nested dict."""
    uid = user.telegram_id

    accounts = list(
        (
            await session.execute(
                select(Account)
                .where(Account.user_id == uid)
                .order_by(Account.created_at)
            )
        )
        .scalars()
        .all()
    )
    categories = list(
        (
            await session.execute(
                select(Category)
                .where(Category.user_id == uid)
                .order_by(Category.name_en)
            )
        )
        .scalars()
        .all()
    )
    transactions = list(
        (
            await session.execute(
                select(Transaction)
                .where(
                    Transaction.user_id == uid,
                    Transaction.is_deleted.is_(False),
                )
                .order_by(Transaction.occurred_at.desc())
            )
        )
        .scalars()
        .all()
    )
    budgets = list(
        (
            await session.execute(
                select(Budget)
                .where(Budget.user_id == uid)
                .order_by(Budget.created_at)
            )
        )
        .scalars()
        .all()
    )
    goals = list(
        (
            await session.execute(
                select(SavingsGoal)
                .where(SavingsGoal.user_id == uid)
                .order_by(SavingsGoal.created_at)
            )
        )
        .scalars()
        .all()
    )
    credit_history = list(
        (
            await session.execute(
                select(CreditTransaction)
                .where(CreditTransaction.user_id == uid)
                .order_by(CreditTransaction.created_at.desc())
            )
        )
        .scalars()
        .all()
    )

    return {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "generated_at": datetime.now(tz=user.created_at.tzinfo).isoformat()
        if user.created_at.tzinfo
        else datetime.utcnow().isoformat(),
        "user": {
            "telegram_id": user.telegram_id,
            "username": user.username,
            "display_name": user.display_name,
            "language_code": user.language_code,
            "timezone": user.timezone,
            "calendar_system": user.calendar_system,
            "default_currency": user.default_currency,
            "credit_balance": user.credit_balance,
            "onboarding_completed": user.onboarding_completed,
            "created_at": user.created_at,
        },
        "accounts": [
            _row(
                a,
                [
                    "id",
                    "name",
                    "type",
                    "currency",
                    "current_balance",
                    "icon",
                    "color",
                    "is_archived",
                    "is_default",
                    "is_default_income",
                    "created_at",
                ],
            )
            for a in accounts
        ],
        "categories": [
            _row(
                c,
                [
                    "id",
                    "name",
                    "name_en",
                    "name_fa",
                    "type",
                    "parent_id",
                    "icon",
                    "color",
                    "is_archived",
                ],
            )
            for c in categories
        ],
        "transactions": [
            _row(
                t,
                [
                    "id",
                    "account_id",
                    "category_id",
                    "type",
                    "amount",
                    "currency",
                    "merchant",
                    "description",
                    "occurred_at",
                    "to_account_id",
                    "source",
                    "created_at",
                ],
            )
            for t in transactions
        ],
        "budgets": [
            _row(
                b,
                [
                    "id",
                    "category_id",
                    "amount",
                    "currency",
                    "period",
                    "is_active",
                    "created_at",
                ],
            )
            for b in budgets
        ],
        "savings_goals": [
            _row(
                g,
                [
                    "id",
                    "name",
                    "icon",
                    "target_amount",
                    "current_amount",
                    "currency",
                    "deadline",
                    "linked_account_id",
                    "is_completed",
                    "created_at",
                ],
            )
            for g in goals
        ],
        "credit_history": [
            _row(
                h,
                [
                    "id",
                    "change_amount",
                    "balance_after",
                    "reason",
                    "reference_id",
                    "ai_tokens_used",
                    "ai_provider",
                    "ai_model",
                    "cost_usd",
                    "created_at",
                ],
            )
            for h in credit_history
        ],
    }


async def build_transactions_csv(
    session: AsyncSession, *, user: User
) -> str:
    """A spreadsheet-ready view of the user's transactions.

    Column set is fixed and self-documenting; missing values are empty strings,
    not "None". Amounts are printed with their native precision.
    """
    uid = user.telegram_id
    accounts = {
        a.id: a
        for a in (
            await session.execute(
                select(Account).where(Account.user_id == uid)
            )
        )
        .scalars()
        .all()
    }
    categories = {
        c.id: c
        for c in (
            await session.execute(
                select(Category).where(Category.user_id == uid)
            )
        )
        .scalars()
        .all()
    }
    transactions = list(
        (
            await session.execute(
                select(Transaction)
                .where(
                    Transaction.user_id == uid,
                    Transaction.is_deleted.is_(False),
                )
                .order_by(Transaction.occurred_at.desc())
            )
        )
        .scalars()
        .all()
    )

    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(
        [
            "occurred_at",
            "type",
            "amount",
            "currency",
            "category",
            "account",
            "to_account",
            "description",
            "merchant",
            "source",
        ]
    )
    for t in transactions:
        cat = categories.get(t.category_id) if t.category_id else None
        acct = accounts.get(t.account_id)
        to_acct = accounts.get(t.to_account_id) if t.to_account_id else None
        writer.writerow(
            [
                t.occurred_at.isoformat(),
                t.type.value if hasattr(t.type, "value") else t.type,
                str(t.amount),
                t.currency,
                cat.name if cat else "",
                acct.name if acct else "",
                to_acct.name if to_acct else "",
                t.description or "",
                t.merchant or "",
                t.source.value if hasattr(t.source, "value") else t.source,
            ]
        )
    return buf.getvalue()
