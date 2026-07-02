"""Read-only analytics queries — all aggregations computed by SQL, never the LLM."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.budget import Budget
from app.models.category import Category, CategoryType
from app.models.savings_goal import SavingsGoal
from app.models.shared_expense import (
    SharedExpense,
    SharedExpenseSplit,
    SplitStatus,
)
from app.models.transaction import Transaction, TransactionType
from app.services.budget_service import period_bounds


# ---------- Balances / counts (kept from earlier) ----------


async def get_balances_by_currency(
    session: AsyncSession, user_id: int
) -> dict[str, Decimal]:
    stmt = (
        select(Account.currency, func.coalesce(func.sum(Account.current_balance), 0))
        .where(Account.user_id == user_id, Account.is_archived.is_(False))
        .group_by(Account.currency)
    )
    result = await session.execute(stmt)
    return {currency: total for currency, total in result.all()}


async def count_active_accounts(session: AsyncSession, user_id: int) -> int:
    stmt = (
        select(func.count())
        .select_from(Account)
        .where(Account.user_id == user_id, Account.is_archived.is_(False))
    )
    return int((await session.execute(stmt)).scalar_one())


# ---------- Period helpers ----------


def _tz(tz_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def _today_local(tz_name: str) -> date:
    return datetime.now(UTC).astimezone(_tz(tz_name)).date()


def bounds_for_period(
    period: str, tz_name: str
) -> tuple[datetime, datetime]:
    """[start, end) UTC-aware bounds for a named report period."""
    tz = _tz(tz_name)
    now_local = datetime.now(UTC).astimezone(tz)

    if period == "week":
        start_local = (now_local - timedelta(days=now_local.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end_local = start_local + timedelta(days=7)
    elif period == "month":
        start_local = now_local.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        if now_local.month == 12:
            end_local = start_local.replace(year=now_local.year + 1, month=1)
        else:
            end_local = start_local.replace(month=now_local.month + 1)
    elif period == "quarter":
        quarter_start_month = ((now_local.month - 1) // 3) * 3 + 1
        start_local = now_local.replace(
            month=quarter_start_month,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        end_month = quarter_start_month + 3
        if end_month > 12:
            end_local = start_local.replace(year=now_local.year + 1, month=end_month - 12)
        else:
            end_local = start_local.replace(month=end_month)
    elif period == "year":
        start_local = now_local.replace(
            month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )
        end_local = start_local.replace(year=now_local.year + 1)
    else:
        raise ValueError(f"unknown period: {period}")

    return start_local.astimezone(UTC), end_local.astimezone(UTC)


# ---------- Category breakdown ----------


@dataclass(frozen=True)
class CategoryTotal:
    category_id: str
    name: str
    icon: str
    amount: Decimal
    currency: str


async def get_spending_by_category(
    session: AsyncSession,
    *,
    user_id: int,
    start: datetime,
    end: datetime,
    limit: int | None = None,
) -> list[CategoryTotal]:
    """Expense totals grouped by category for the window. Ordered by amount desc."""
    stmt = (
        select(
            Category.id,
            Category.name,
            Category.icon,
            Transaction.currency,
            func.sum(Transaction.amount).label("total"),
        )
        .join(Category, Category.id == Transaction.category_id)
        .where(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.is_deleted.is_(False),
            Transaction.occurred_at >= start,
            Transaction.occurred_at < end,
        )
        .group_by(Category.id, Category.name, Category.icon, Transaction.currency)
        .order_by(func.sum(Transaction.amount).desc())
    )
    if limit is not None:
        stmt = stmt.limit(limit)
    rows = (await session.execute(stmt)).all()
    return [
        CategoryTotal(
            category_id=str(r[0]),
            name=r[1],
            icon=r[2],
            amount=Decimal(str(r[4])),
            currency=r[3],
        )
        for r in rows
    ]


# ---------- Income vs expense (per-currency because we don't FX-convert yet) ----------


@dataclass(frozen=True)
class DirectionTotal:
    income: Decimal
    expense: Decimal


async def get_income_vs_expense(
    session: AsyncSession,
    *,
    user_id: int,
    start: datetime,
    end: datetime,
) -> dict[str, DirectionTotal]:
    """Per-currency income and expense totals within [start, end)."""
    income_expr = func.coalesce(
        func.sum(
            case((Transaction.type == TransactionType.INCOME, Transaction.amount), else_=0)
        ),
        0,
    )
    expense_expr = func.coalesce(
        func.sum(
            case((Transaction.type == TransactionType.EXPENSE, Transaction.amount), else_=0)
        ),
        0,
    )
    stmt = (
        select(Transaction.currency, income_expr, expense_expr)
        .where(
            Transaction.user_id == user_id,
            Transaction.is_deleted.is_(False),
            Transaction.occurred_at >= start,
            Transaction.occurred_at < end,
        )
        .group_by(Transaction.currency)
    )
    rows = (await session.execute(stmt)).all()
    return {
        r[0]: DirectionTotal(income=Decimal(str(r[1])), expense=Decimal(str(r[2])))
        for r in rows
    }


# ---------- Trend series ----------


@dataclass(frozen=True)
class MonthBucket:
    year: int
    month: int
    income: Decimal
    expense: Decimal


async def get_monthly_trend(
    session: AsyncSession,
    *,
    user_id: int,
    months_back: int = 6,
    tz_name: str = "UTC",
    currency: str | None = None,
) -> list[MonthBucket]:
    """Month-by-month income and expense for the last N months, ordered oldest first.

    Bucket boundaries respect the user's timezone; totals for currencies other
    than the passed `currency` (if any) are excluded. When `currency` is None,
    every currency contributes to the same bucket (typically only useful when
    the user is single-currency).
    """
    tz = _tz(tz_name)
    today_local = datetime.now(UTC).astimezone(tz)
    start_month = today_local.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    # Walk back months_back-1 months so we return `months_back` total buckets
    # including the current month.
    for _ in range(months_back - 1):
        prev = start_month - timedelta(days=1)
        start_month = prev.replace(day=1)
    start_utc = start_month.astimezone(UTC)

    conditions = [
        Transaction.user_id == user_id,
        Transaction.is_deleted.is_(False),
        Transaction.occurred_at >= start_utc,
    ]
    if currency:
        conditions.append(Transaction.currency == currency)

    # Group by (year, month) computed in the user's timezone.
    year_expr = func.extract("year", func.timezone(tz_name, Transaction.occurred_at))
    month_expr = func.extract("month", func.timezone(tz_name, Transaction.occurred_at))

    income_expr = func.coalesce(
        func.sum(
            case((Transaction.type == TransactionType.INCOME, Transaction.amount), else_=0)
        ),
        0,
    )
    expense_expr = func.coalesce(
        func.sum(
            case((Transaction.type == TransactionType.EXPENSE, Transaction.amount), else_=0)
        ),
        0,
    )

    stmt = (
        select(year_expr, month_expr, income_expr, expense_expr)
        .where(*conditions)
        .group_by(year_expr, month_expr)
    )
    rows = (await session.execute(stmt)).all()
    got = {
        (int(y), int(m)): (Decimal(str(i)), Decimal(str(e)))
        for y, m, i, e in rows
    }

    # Emit buckets in order, even if empty.
    buckets: list[MonthBucket] = []
    cursor = start_month
    while cursor <= today_local:
        income, expense = got.get((cursor.year, cursor.month), (Decimal(0), Decimal(0)))
        buckets.append(
            MonthBucket(
                year=cursor.year,
                month=cursor.month,
                income=income,
                expense=expense,
            )
        )
        # advance one month
        if cursor.month == 12:
            cursor = cursor.replace(year=cursor.year + 1, month=1)
        else:
            cursor = cursor.replace(month=cursor.month + 1)

    return buckets


# ---------- Savings rate ----------


async def get_savings_rate(
    session: AsyncSession,
    *,
    user_id: int,
    start: datetime,
    end: datetime,
) -> float:
    """(income - expense) / income across all currencies. 0 when income is 0."""
    totals = await get_income_vs_expense(
        session, user_id=user_id, start=start, end=end
    )
    income = sum((t.income for t in totals.values()), Decimal(0))
    expense = sum((t.expense for t in totals.values()), Decimal(0))
    if income <= 0:
        return 0.0
    return float((income - expense) / income)


# ---------- Behavior score ----------


@dataclass(frozen=True)
class BehaviorScore:
    total: int
    logging_consistency: int
    budget_adherence: int
    savings_rate: int
    debt_free: int
    goal_progress: int


async def _logged_days_last_30(
    session: AsyncSession, *, user_id: int, tz_name: str
) -> int:
    tz = _tz(tz_name)
    now_local = datetime.now(UTC).astimezone(tz)
    start_local = (now_local - timedelta(days=29)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    start_utc = start_local.astimezone(UTC)

    day_expr = func.date_trunc("day", func.timezone(tz_name, Transaction.occurred_at))
    stmt = (
        select(func.count(func.distinct(day_expr)))
        .where(
            Transaction.user_id == user_id,
            Transaction.is_deleted.is_(False),
            Transaction.occurred_at >= start_utc,
        )
    )
    return int((await session.execute(stmt)).scalar_one())


async def _budget_adherence_ratio(
    session: AsyncSession, *, user_id: int, tz_name: str
) -> float:
    from app.services.budget_service import get_usage

    stmt = select(Budget).where(
        Budget.user_id == user_id, Budget.is_active.is_(True)
    )
    budgets = list((await session.execute(stmt)).scalars().all())
    if not budgets:
        return 1.0
    within = 0
    for budget in budgets:
        usage = await get_usage(session, budget=budget, tz_name=tz_name)
        if usage.ratio <= 1:
            within += 1
    return within / len(budgets)


async def _has_open_debt(session: AsyncSession, user_id: int) -> bool:
    """Any approved (unsettled) shared-expense split where this user owes."""
    stmt = (
        select(SharedExpenseSplit.id)
        .join(
            SharedExpense,
            SharedExpense.id == SharedExpenseSplit.shared_expense_id,
        )
        .where(
            SharedExpenseSplit.user_id == user_id,
            SharedExpense.created_by_user_id != user_id,
            SharedExpenseSplit.status == SplitStatus.APPROVED,
        )
        .limit(1)
    )
    return (await session.execute(stmt)).first() is not None


async def _has_goal_progress(session: AsyncSession, user_id: int) -> bool:
    stmt = select(SavingsGoal.id).where(
        SavingsGoal.user_id == user_id,
        SavingsGoal.current_amount > Decimal(0),
    )
    return (await session.execute(stmt)).first() is not None


async def compute_behavior_score(
    session: AsyncSession, *, user_id: int, tz_name: str
) -> BehaviorScore:
    # Logging consistency (30 pts). Full points at >=80% (24/30 days).
    logged_days = await _logged_days_last_30(session, user_id=user_id, tz_name=tz_name)
    ratio_days = logged_days / 30
    if ratio_days >= 0.8:
        logging_pts = 30
    else:
        logging_pts = round((ratio_days / 0.8) * 30)

    # Budget adherence (25 pts). No active budgets → full credit.
    adherence = await _budget_adherence_ratio(session, user_id=user_id, tz_name=tz_name)
    budget_pts = round(adherence * 25)

    # Savings rate over last 30 days (25 pts). 20%+ = full points, else linear.
    now = datetime.now(UTC)
    savings = await get_savings_rate(
        session, user_id=user_id, start=now - timedelta(days=30), end=now
    )
    if savings >= 0.2:
        savings_pts = 25
    elif savings <= 0:
        savings_pts = 0
    else:
        savings_pts = round((savings / 0.2) * 25)

    # Debt-free (10 pts).
    debt_pts = 0 if await _has_open_debt(session, user_id) else 10

    # Goal progress (10 pts).
    goal_pts = 10 if await _has_goal_progress(session, user_id) else 0

    return BehaviorScore(
        total=logging_pts + budget_pts + savings_pts + debt_pts + goal_pts,
        logging_consistency=logging_pts,
        budget_adherence=budget_pts,
        savings_rate=savings_pts,
        debt_free=debt_pts,
        goal_progress=goal_pts,
    )


# ---------- Monthly comparison ----------


@dataclass(frozen=True)
class MonthlyComparison:
    this_month_expense: Decimal
    last_month_expense: Decimal
    delta_pct: float | None
    currency: str | None


async def get_monthly_comparison(
    session: AsyncSession, *, user_id: int, tz_name: str, currency: str | None
) -> MonthlyComparison:
    tz = _tz(tz_name)
    now_local = datetime.now(UTC).astimezone(tz)

    this_start_local = now_local.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    if now_local.month == 12:
        next_start_local = this_start_local.replace(year=now_local.year + 1, month=1)
    else:
        next_start_local = this_start_local.replace(month=now_local.month + 1)
    prev_end_local = this_start_local
    if this_start_local.month == 1:
        prev_start_local = this_start_local.replace(
            year=this_start_local.year - 1, month=12
        )
    else:
        prev_start_local = this_start_local.replace(month=this_start_local.month - 1)

    async def _sum_expense(start: datetime, end: datetime) -> Decimal:
        conditions = [
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.is_deleted.is_(False),
            Transaction.occurred_at >= start.astimezone(UTC),
            Transaction.occurred_at < end.astimezone(UTC),
        ]
        if currency:
            conditions.append(Transaction.currency == currency)
        stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(*conditions)
        return Decimal(str((await session.execute(stmt)).scalar_one()))

    this_month = await _sum_expense(this_start_local, next_start_local)
    last_month = await _sum_expense(prev_start_local, prev_end_local)
    delta_pct: float | None = None
    if last_month > 0:
        delta_pct = float((this_month - last_month) / last_month)
    return MonthlyComparison(
        this_month_expense=this_month,
        last_month_expense=last_month,
        delta_pct=delta_pct,
        currency=currency,
    )
