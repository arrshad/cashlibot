"""Savings goals: CRUD + contribution tracking."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.savings_goal import SavingsGoal


class SavingsError(ValueError):
    """User-facing savings error."""


# ---------- CRUD ----------


async def create_goal(
    session: AsyncSession,
    *,
    user_id: int,
    name: str,
    target_amount: Decimal,
    currency: str,
    icon: str = "fa-piggy-bank",
    deadline: date | None = None,
    linked_account_id: uuid.UUID | None = None,
) -> SavingsGoal:
    name = name.strip()
    if not name:
        raise SavingsError("name is required")
    if target_amount <= 0:
        raise SavingsError("target_amount must be positive")

    if linked_account_id is not None:
        if not await _account_belongs(session, linked_account_id, user_id):
            raise SavingsError("linked account not found")

    goal = SavingsGoal(
        user_id=user_id,
        name=name,
        target_amount=target_amount,
        currency=currency,
        icon=icon,
        deadline=deadline,
        linked_account_id=linked_account_id,
    )
    session.add(goal)
    await session.flush()
    return goal


async def get_goal(
    session: AsyncSession, *, goal_id: uuid.UUID, user_id: int
) -> SavingsGoal | None:
    goal = await session.get(SavingsGoal, goal_id)
    if goal is None or goal.user_id != user_id:
        return None
    return goal


async def list_goals(
    session: AsyncSession,
    user_id: int,
    *,
    include_completed: bool = True,
) -> list[SavingsGoal]:
    stmt = select(SavingsGoal).where(SavingsGoal.user_id == user_id)
    if not include_completed:
        stmt = stmt.where(SavingsGoal.is_completed.is_(False))
    stmt = stmt.order_by(SavingsGoal.created_at)
    return list((await session.execute(stmt)).scalars().all())


_EDITABLE_FIELDS = {"name", "icon", "target_amount", "deadline", "linked_account_id"}


async def update_goal(
    session: AsyncSession,
    *,
    goal: SavingsGoal,
    fields: dict[str, object],
) -> SavingsGoal:
    unknown = set(fields) - _EDITABLE_FIELDS
    if unknown:
        raise SavingsError(f"cannot edit {sorted(unknown)}")

    if "target_amount" in fields:
        amount = fields["target_amount"]
        if isinstance(amount, Decimal) and amount <= 0:
            raise SavingsError("target_amount must be positive")

    if "linked_account_id" in fields:
        acct_id = fields["linked_account_id"]
        if acct_id is not None and not await _account_belongs(
            session, acct_id, goal.user_id  # type: ignore[arg-type]
        ):
            raise SavingsError("linked account not found")

    for key, value in fields.items():
        setattr(goal, key, value)

    # Re-check completion status against the (possibly new) target.
    goal.is_completed = goal.current_amount >= goal.target_amount

    session.add(goal)
    await session.flush()
    return goal


async def delete_goal(session: AsyncSession, goal: SavingsGoal) -> None:
    await session.delete(goal)
    await session.flush()


# ---------- contributions ----------


async def add_contribution(
    session: AsyncSession, *, goal: SavingsGoal, amount: Decimal
) -> tuple[SavingsGoal, bool]:
    """Increment current_amount. Returns (goal, just_completed)."""
    if amount <= 0:
        raise SavingsError("amount must be positive")

    was_completed = goal.is_completed
    goal.current_amount = goal.current_amount + amount
    if goal.current_amount >= goal.target_amount:
        goal.is_completed = True
    session.add(goal)
    await session.flush()
    return goal, (goal.is_completed and not was_completed)


# ---------- internals ----------


async def _account_belongs(
    session: AsyncSession, account_id: uuid.UUID, user_id: int
) -> bool:
    stmt = select(Account.id).where(
        Account.id == account_id, Account.user_id == user_id
    )
    return (await session.execute(stmt)).scalar_one_or_none() is not None
