"""Budgets CRUD + usage."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.core.bootstrap import load_app_context
from app.models.budget import Budget, BudgetPeriod
from app.models.user import User
from app.services.budget_service import (
    BudgetError,
    BudgetUsage,
    create_budget,
    delete_budget,
    get_budget,
    list_with_usage,
)

router = APIRouter(prefix="/budgets")


class BudgetOut(BaseModel):
    id: uuid.UUID
    category_id: uuid.UUID
    amount: Decimal
    spent: Decimal
    ratio: float
    currency: str
    period: BudgetPeriod
    is_active: bool
    period_start: datetime
    period_end: datetime

    @classmethod
    def from_usage(cls, u: BudgetUsage) -> "BudgetOut":
        b = u.budget
        return cls(
            id=b.id,
            category_id=b.category_id,
            amount=b.amount,
            spent=u.spent,
            ratio=float(u.ratio),
            currency=b.currency,
            period=b.period,
            is_active=b.is_active,
            period_start=u.period_start,
            period_end=u.period_end,
        )


class BudgetCreateIn(BaseModel):
    category_id: uuid.UUID
    amount: Decimal = Field(gt=Decimal(0))
    currency: str = Field(min_length=2, max_length=5)
    period: BudgetPeriod


@router.get("", response_model=list[BudgetOut])
async def list_my_budgets(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[BudgetOut]:
    usages = await list_with_usage(session, user_id=user.telegram_id, tz_name=user.timezone)
    return [BudgetOut.from_usage(u) for u in usages]


@router.post("", response_model=BudgetOut, status_code=status.HTTP_201_CREATED)
async def create_my_budget(
    payload: BudgetCreateIn,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BudgetOut:
    ctx = load_app_context()
    if not ctx.currencies.is_enabled(payload.currency):
        raise HTTPException(400, f"unknown currency: {payload.currency}")

    try:
        budget = await create_budget(
            session,
            user_id=user.telegram_id,
            category_id=payload.category_id,
            amount=payload.amount,
            currency=payload.currency,
            period=payload.period,
        )
    except BudgetError as exc:
        raise HTTPException(400, str(exc)) from exc

    # Return the new budget with its current usage snapshot.
    from app.services.budget_service import get_usage

    usage = await get_usage(session, budget=budget, tz_name=user.timezone)
    return BudgetOut.from_usage(usage)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_budget(
    budget_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    budget = await get_budget(
        session, budget_id=budget_id, user_id=user.telegram_id
    )
    if budget is None:
        raise HTTPException(404, "budget not found")
    await delete_budget(session, budget)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
