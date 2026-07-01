"""Savings goals CRUD + contribute."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.core.bootstrap import load_app_context
from app.models.savings_goal import SavingsGoal
from app.models.user import User
from app.services.savings_service import (
    SavingsError,
    add_contribution,
    create_goal,
    delete_goal,
    get_goal,
    list_goals,
    update_goal,
)

router = APIRouter(prefix="/goals")


class GoalOut(BaseModel):
    id: uuid.UUID
    name: str
    icon: str
    target_amount: Decimal
    current_amount: Decimal
    currency: str
    deadline: date | None
    linked_account_id: uuid.UUID | None
    is_completed: bool
    created_at: datetime

    @classmethod
    def from_model(cls, g: SavingsGoal) -> "GoalOut":
        return cls(
            id=g.id,
            name=g.name,
            icon=g.icon,
            target_amount=g.target_amount,
            current_amount=g.current_amount,
            currency=g.currency,
            deadline=g.deadline,
            linked_account_id=g.linked_account_id,
            is_completed=g.is_completed,
            created_at=g.created_at,
        )


class GoalCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    target_amount: Decimal = Field(gt=Decimal(0))
    currency: str = Field(min_length=2, max_length=5)
    icon: str | None = Field(default=None, max_length=64)
    deadline: date | None = None
    linked_account_id: uuid.UUID | None = None


class GoalPatchIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=60)
    icon: str | None = Field(default=None, max_length=64)
    target_amount: Decimal | None = Field(default=None, gt=Decimal(0))
    deadline: date | None = None
    linked_account_id: uuid.UUID | None = None


class ContributeIn(BaseModel):
    amount: Decimal = Field(gt=Decimal(0))


class ContributeOut(BaseModel):
    goal: GoalOut
    just_completed: bool


@router.get("", response_model=list[GoalOut])
async def list_my_goals(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[GoalOut]:
    goals = await list_goals(session, user.telegram_id)
    return [GoalOut.from_model(g) for g in goals]


@router.post("", response_model=GoalOut, status_code=status.HTTP_201_CREATED)
async def create_my_goal(
    payload: GoalCreateIn,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> GoalOut:
    ctx = load_app_context()
    if not ctx.currencies.is_enabled(payload.currency):
        raise HTTPException(400, f"unknown currency: {payload.currency}")

    try:
        goal = await create_goal(
            session,
            user_id=user.telegram_id,
            name=payload.name,
            target_amount=payload.target_amount,
            currency=payload.currency,
            icon=payload.icon or "fa-piggy-bank",
            deadline=payload.deadline,
            linked_account_id=payload.linked_account_id,
        )
    except SavingsError as exc:
        raise HTTPException(400, str(exc)) from exc
    return GoalOut.from_model(goal)


@router.patch("/{goal_id}", response_model=GoalOut)
async def update_my_goal(
    goal_id: uuid.UUID,
    payload: GoalPatchIn,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> GoalOut:
    goal = await get_goal(session, goal_id=goal_id, user_id=user.telegram_id)
    if goal is None:
        raise HTTPException(404, "goal not found")
    fields = payload.model_dump(exclude_unset=True)
    if not fields:
        return GoalOut.from_model(goal)
    try:
        updated = await update_goal(session, goal=goal, fields=fields)
    except SavingsError as exc:
        raise HTTPException(400, str(exc)) from exc
    return GoalOut.from_model(updated)


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_goal(
    goal_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    goal = await get_goal(session, goal_id=goal_id, user_id=user.telegram_id)
    if goal is None:
        raise HTTPException(404, "goal not found")
    await delete_goal(session, goal)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{goal_id}/contribute", response_model=ContributeOut)
async def contribute_to_my_goal(
    goal_id: uuid.UUID,
    payload: ContributeIn,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ContributeOut:
    goal = await get_goal(session, goal_id=goal_id, user_id=user.telegram_id)
    if goal is None:
        raise HTTPException(404, "goal not found")
    try:
        updated, just_completed = await add_contribution(
            session, goal=goal, amount=payload.amount
        )
    except SavingsError as exc:
        raise HTTPException(400, str(exc)) from exc
    return ContributeOut(goal=GoalOut.from_model(updated), just_completed=just_completed)
