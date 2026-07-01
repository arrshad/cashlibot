"""Budgets: CRUD, usage, and threshold-crossing detection."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import Budget, BudgetPeriod
from app.models.category import Category
from app.models.transaction import Transaction, TransactionType


class BudgetError(ValueError):
    """User-facing budget error (unknown category, currency, etc.)."""


# 90% "amber" — start paying attention. 100% "red" — over budget.
WARN_RATIO = Decimal("0.90")
EXCEED_RATIO = Decimal("1.00")

ThresholdLevel = Literal["warning", "exceeded"]


@dataclass(frozen=True)
class BudgetUsage:
    budget: Budget
    spent: Decimal
    ratio: Decimal   # spent / amount (can exceed 1)
    period_start: datetime
    period_end: datetime


@dataclass(frozen=True)
class ThresholdCrossing:
    budget: Budget
    level: ThresholdLevel
    spent: Decimal
    limit: Decimal


# ---------- period math ----------


def period_bounds(
    period: BudgetPeriod, tz_name: str, ref: datetime | None = None
) -> tuple[datetime, datetime]:
    """[start, end) for the current period in the user's local timezone.

    Returned datetimes are timezone-aware and expressed in UTC so they can be
    handed straight to SQLAlchemy against a `DateTime(timezone=True)` column.
    """
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        tz = ZoneInfo("UTC")

    now_local = (ref or datetime.now(UTC)).astimezone(tz)

    if period == BudgetPeriod.WEEKLY:
        start_date = now_local.date() - timedelta(days=now_local.weekday())
        start_local = datetime.combine(start_date, datetime.min.time(), tzinfo=tz)
        end_local = start_local + timedelta(days=7)
    elif period == BudgetPeriod.MONTHLY:
        start_local = now_local.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        if now_local.month == 12:
            end_local = start_local.replace(year=now_local.year + 1, month=1)
        else:
            end_local = start_local.replace(month=now_local.month + 1)
    elif period == BudgetPeriod.YEARLY:
        start_local = now_local.replace(
            month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )
        end_local = start_local.replace(year=now_local.year + 1)
    else:  # pragma: no cover
        raise ValueError(f"unknown period: {period}")

    return start_local.astimezone(UTC), end_local.astimezone(UTC)


# ---------- CRUD ----------


async def create_budget(
    session: AsyncSession,
    *,
    user_id: int,
    category_id: uuid.UUID,
    amount: Decimal,
    currency: str,
    period: BudgetPeriod,
) -> Budget:
    if amount <= 0:
        raise BudgetError("amount must be positive")

    if not await _category_belongs(session, category_id, user_id):
        raise BudgetError("category not found")

    # Uniqueness on (user, category, period): if one already exists, update it.
    existing_stmt = select(Budget).where(
        Budget.user_id == user_id,
        Budget.category_id == category_id,
        Budget.period == period,
    )
    existing = (await session.execute(existing_stmt)).scalars().first()
    if existing is not None:
        existing.amount = amount
        existing.currency = currency
        existing.is_active = True
        session.add(existing)
        await session.flush()
        return existing

    budget = Budget(
        user_id=user_id,
        category_id=category_id,
        amount=amount,
        currency=currency,
        period=period,
    )
    session.add(budget)
    await session.flush()
    return budget


async def get_budget(
    session: AsyncSession, *, budget_id: uuid.UUID, user_id: int
) -> Budget | None:
    b = await session.get(Budget, budget_id)
    if b is None or b.user_id != user_id:
        return None
    return b


async def list_budgets(
    session: AsyncSession, user_id: int, *, include_inactive: bool = False
) -> list[Budget]:
    stmt = select(Budget).where(Budget.user_id == user_id)
    if not include_inactive:
        stmt = stmt.where(Budget.is_active.is_(True))
    stmt = stmt.order_by(Budget.created_at)
    return list((await session.execute(stmt)).scalars().all())


async def delete_budget(session: AsyncSession, budget: Budget) -> None:
    await session.delete(budget)
    await session.flush()


# ---------- usage ----------


async def _sum_expenses(
    session: AsyncSession,
    *,
    user_id: int,
    category_id: uuid.UUID,
    start: datetime,
    end: datetime,
) -> Decimal:
    stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.user_id == user_id,
        Transaction.category_id == category_id,
        Transaction.type == TransactionType.EXPENSE,
        Transaction.is_deleted.is_(False),
        Transaction.occurred_at >= start,
        Transaction.occurred_at < end,
    )
    return Decimal(str((await session.execute(stmt)).scalar_one()))


async def get_usage(
    session: AsyncSession, *, budget: Budget, tz_name: str
) -> BudgetUsage:
    start, end = period_bounds(budget.period, tz_name)
    spent = await _sum_expenses(
        session,
        user_id=budget.user_id,
        category_id=budget.category_id,
        start=start,
        end=end,
    )
    ratio = spent / budget.amount if budget.amount > 0 else Decimal(0)
    return BudgetUsage(budget=budget, spent=spent, ratio=ratio, period_start=start, period_end=end)


async def list_with_usage(
    session: AsyncSession, *, user_id: int, tz_name: str
) -> list[BudgetUsage]:
    budgets = await list_budgets(session, user_id)
    return [await get_usage(session, budget=b, tz_name=tz_name) for b in budgets]


# ---------- threshold detection ----------


async def check_after_expense(
    session: AsyncSession,
    *,
    user_id: int,
    category_id: uuid.UUID | None,
    added_amount: Decimal,
    tz_name: str,
) -> ThresholdCrossing | None:
    """After confirming an expense, return the crossing (if any) for its budget.

    Only surfaces a crossing when this specific transaction pushed usage from
    below the threshold to at or above it — repeated warnings for the same
    period aren't sent.
    """
    if category_id is None or added_amount <= 0:
        return None

    stmt = select(Budget).where(
        Budget.user_id == user_id,
        Budget.category_id == category_id,
        Budget.is_active.is_(True),
    )
    budget = (await session.execute(stmt)).scalars().first()
    if budget is None:
        return None

    usage = await get_usage(session, budget=budget, tz_name=tz_name)
    prev_spent = usage.spent - added_amount
    prev_ratio = prev_spent / budget.amount if budget.amount > 0 else Decimal(0)

    if prev_ratio < EXCEED_RATIO <= usage.ratio:
        return ThresholdCrossing(
            budget=budget, level="exceeded", spent=usage.spent, limit=budget.amount
        )
    if prev_ratio < WARN_RATIO <= usage.ratio:
        return ThresholdCrossing(
            budget=budget, level="warning", spent=usage.spent, limit=budget.amount
        )
    return None


# ---------- internal helpers ----------


async def _category_belongs(
    session: AsyncSession, category_id: uuid.UUID, user_id: int
) -> bool:
    stmt = select(Category.id).where(
        Category.id == category_id, Category.user_id == user_id
    )
    return (await session.execute(stmt)).scalar_one_or_none() is not None
