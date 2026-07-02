"""GET /api/reports/... — behavior score + spending summary."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.models.user import User
from app.services.analytics_service import (
    bounds_for_period,
    compute_behavior_score,
    get_income_vs_expense,
    get_monthly_comparison,
    get_monthly_trend,
    get_savings_rate,
    get_spending_by_category,
)

router = APIRouter(prefix="/reports")

Period = Literal["week", "month", "quarter", "year"]


class BehaviorScoreOut(BaseModel):
    total: int
    logging_consistency: int
    budget_adherence: int
    savings_rate: int
    debt_free: int
    goal_progress: int


class CategoryTotalOut(BaseModel):
    category_id: str
    name: str
    icon: str
    amount: Decimal
    currency: str


class DirectionTotalOut(BaseModel):
    currency: str
    income: Decimal
    expense: Decimal


class MonthBucketOut(BaseModel):
    year: int
    month: int
    income: Decimal
    expense: Decimal


class MonthlyComparisonOut(BaseModel):
    this_month_expense: Decimal
    last_month_expense: Decimal
    delta_pct: float | None
    currency: str | None


class SummaryOut(BaseModel):
    period: Period
    period_start: datetime
    period_end: datetime
    by_category: list[CategoryTotalOut]
    income_vs_expense: list[DirectionTotalOut]
    savings_rate: float
    monthly_trend: list[MonthBucketOut]
    monthly_comparison: MonthlyComparisonOut
    behavior_score: BehaviorScoreOut


@router.get("/behavior-score", response_model=BehaviorScoreOut)
async def get_behavior(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BehaviorScoreOut:
    score = await compute_behavior_score(
        session, user_id=user.telegram_id, tz_name=user.timezone
    )
    return BehaviorScoreOut(
        total=score.total,
        logging_consistency=score.logging_consistency,
        budget_adherence=score.budget_adherence,
        savings_rate=score.savings_rate,
        debt_free=score.debt_free,
        goal_progress=score.goal_progress,
    )


@router.get("/summary", response_model=SummaryOut)
async def get_summary(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    period: Annotated[Period, Query()] = "month",
) -> SummaryOut:
    try:
        start, end = bounds_for_period(period, user.timezone)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    by_category = await get_spending_by_category(
        session, user_id=user.telegram_id, start=start, end=end
    )
    iv_expense = await get_income_vs_expense(
        session, user_id=user.telegram_id, start=start, end=end
    )
    savings = await get_savings_rate(
        session, user_id=user.telegram_id, start=start, end=end
    )
    trend = await get_monthly_trend(
        session,
        user_id=user.telegram_id,
        months_back=6,
        tz_name=user.timezone,
        currency=user.default_currency,
    )
    comparison = await get_monthly_comparison(
        session,
        user_id=user.telegram_id,
        tz_name=user.timezone,
        currency=user.default_currency,
    )
    score = await compute_behavior_score(
        session, user_id=user.telegram_id, tz_name=user.timezone
    )

    return SummaryOut(
        period=period,
        period_start=start,
        period_end=end,
        by_category=[
            CategoryTotalOut(
                category_id=c.category_id,
                name=c.name,
                icon=c.icon,
                amount=c.amount,
                currency=c.currency,
            )
            for c in by_category
        ],
        income_vs_expense=[
            DirectionTotalOut(currency=cur, income=d.income, expense=d.expense)
            for cur, d in iv_expense.items()
        ],
        savings_rate=savings,
        monthly_trend=[
            MonthBucketOut(
                year=b.year, month=b.month, income=b.income, expense=b.expense
            )
            for b in trend
        ],
        monthly_comparison=MonthlyComparisonOut(
            this_month_expense=comparison.this_month_expense,
            last_month_expense=comparison.last_month_expense,
            delta_pct=comparison.delta_pct,
            currency=comparison.currency,
        ),
        behavior_score=BehaviorScoreOut(
            total=score.total,
            logging_consistency=score.logging_consistency,
            budget_adherence=score.budget_adherence,
            savings_rate=score.savings_rate,
            debt_free=score.debt_free,
            goal_progress=score.goal_progress,
        ),
    )
