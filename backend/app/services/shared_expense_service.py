"""Shared expenses: create + split approvals + net balance + settlement."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.bootstrap import load_app_context
from app.models.friendship import Friendship, FriendshipStatus
from app.models.shared_expense import (
    SharedExpense,
    SharedExpenseSplit,
    SharedExpenseStatus,
    SplitStatus,
)
from app.models.user import User


class SharedExpenseError(ValueError):
    """User-facing input error."""


@dataclass(frozen=True)
class SplitInput:
    user_id: int
    amount_owed: Decimal


# ---------- Helpers ----------


async def _are_friends(session: AsyncSession, a: int, b: int) -> bool:
    stmt = select(Friendship).where(
        Friendship.status == FriendshipStatus.ACCEPTED,
        or_(
            (Friendship.requester_id == a) & (Friendship.addressee_id == b),
            (Friendship.requester_id == b) & (Friendship.addressee_id == a),
        ),
    )
    return (await session.execute(stmt)).scalars().first() is not None


async def _get_expense(
    session: AsyncSession, expense_id: uuid.UUID
) -> SharedExpense | None:
    return await session.get(SharedExpense, expense_id)


async def _recompute_expense_status(
    session: AsyncSession, expense_id: uuid.UUID
) -> SharedExpense:
    """Bump the parent expense to partially / fully settled based on splits."""
    expense = await session.get(SharedExpense, expense_id)
    if expense is None:
        raise SharedExpenseError("expense not found")

    stmt = select(SharedExpenseSplit).where(
        SharedExpenseSplit.shared_expense_id == expense_id
    )
    splits = list((await session.execute(stmt)).scalars().all())

    if not splits:
        return expense

    all_settled = all(s.status == SplitStatus.SETTLED for s in splits)
    any_settled = any(s.status == SplitStatus.SETTLED for s in splits)

    if all_settled:
        expense.status = SharedExpenseStatus.FULLY_SETTLED
    elif any_settled:
        expense.status = SharedExpenseStatus.PARTIALLY_SETTLED
    else:
        expense.status = SharedExpenseStatus.OPEN
    session.add(expense)
    await session.flush()
    return expense


# ---------- Create ----------


async def create_shared_expense(
    session: AsyncSession,
    *,
    creator: User,
    description: str,
    total_amount: Decimal,
    currency: str,
    splits: list[SplitInput],
) -> tuple[SharedExpense, list[SharedExpenseSplit]]:
    description = description.strip()
    if not description:
        raise SharedExpenseError("description is required")
    if total_amount <= 0:
        raise SharedExpenseError("total_amount must be positive")

    ctx = load_app_context()
    if not ctx.currencies.is_enabled(currency):
        raise SharedExpenseError(f"unknown currency: {currency}")

    if not splits:
        raise SharedExpenseError("at least one participant is required")

    seen: set[int] = set()
    for s in splits:
        if s.user_id == creator.telegram_id:
            raise SharedExpenseError(
                "your own share is implicit — don't include yourself in splits"
            )
        if s.user_id in seen:
            raise SharedExpenseError(
                f"duplicate participant: {s.user_id}"
            )
        seen.add(s.user_id)
        if s.amount_owed <= 0:
            raise SharedExpenseError("each split amount must be positive")
        if not await _are_friends(session, creator.telegram_id, s.user_id):
            raise SharedExpenseError(
                f"{s.user_id} isn't in your friend list"
            )

    splits_total = sum((s.amount_owed for s in splits), Decimal(0))
    if splits_total > total_amount:
        raise SharedExpenseError(
            "split amounts total more than the expense total"
        )

    expense = SharedExpense(
        created_by_user_id=creator.telegram_id,
        description=description,
        total_amount=total_amount,
        currency=currency,
    )
    session.add(expense)
    await session.flush()

    rows = [
        SharedExpenseSplit(
            shared_expense_id=expense.id,
            user_id=s.user_id,
            amount_owed=s.amount_owed,
        )
        for s in splits
    ]
    session.add_all(rows)
    await session.flush()
    return expense, rows


# ---------- Split actions ----------


async def get_split(
    session: AsyncSession, split_id: uuid.UUID
) -> SharedExpenseSplit | None:
    return await session.get(SharedExpenseSplit, split_id)


async def approve_split(
    session: AsyncSession, *, split: SharedExpenseSplit, actor: User
) -> SharedExpenseSplit:
    if split.user_id != actor.telegram_id:
        raise SharedExpenseError("only the debtor can approve this split")
    if split.status not in (SplitStatus.PENDING_APPROVAL, SplitStatus.DISPUTED):
        raise SharedExpenseError("this split is already resolved")

    split.status = SplitStatus.APPROVED
    split.approved_at = datetime.now(UTC)
    session.add(split)
    await session.flush()
    return split


async def dispute_split(
    session: AsyncSession, *, split: SharedExpenseSplit, actor: User
) -> SharedExpenseSplit:
    if split.user_id != actor.telegram_id:
        raise SharedExpenseError("only the debtor can dispute this split")
    if split.status not in (SplitStatus.PENDING_APPROVAL, SplitStatus.APPROVED):
        raise SharedExpenseError("this split can't be disputed anymore")

    split.status = SplitStatus.DISPUTED
    split.approved_at = None
    session.add(split)
    await session.flush()
    return split


# ---------- Listing ----------


async def list_pending_splits_for(
    session: AsyncSession, user_id: int
) -> list[SharedExpenseSplit]:
    """Splits the user needs to answer (approve or dispute)."""
    stmt = (
        select(SharedExpenseSplit)
        .where(
            SharedExpenseSplit.user_id == user_id,
            SharedExpenseSplit.status == SplitStatus.PENDING_APPROVAL,
        )
        .order_by(SharedExpenseSplit.created_at.desc())
    )
    return list((await session.execute(stmt)).scalars().all())


async def list_created_expenses(
    session: AsyncSession, user_id: int
) -> list[SharedExpense]:
    stmt = (
        select(SharedExpense)
        .where(SharedExpense.created_by_user_id == user_id)
        .order_by(SharedExpense.created_at.desc())
    )
    return list((await session.execute(stmt)).scalars().all())


async def list_splits_for_expense(
    session: AsyncSession, expense_id: uuid.UUID
) -> list[SharedExpenseSplit]:
    stmt = (
        select(SharedExpenseSplit)
        .where(SharedExpenseSplit.shared_expense_id == expense_id)
        .order_by(SharedExpenseSplit.created_at)
    )
    return list((await session.execute(stmt)).scalars().all())


async def list_expenses_between(
    session: AsyncSession, user_a: int, user_b: int
) -> list[tuple[SharedExpense, SharedExpenseSplit]]:
    """Every (expense, split-affecting-both) pair between two users."""
    stmt = (
        select(SharedExpense, SharedExpenseSplit)
        .join(
            SharedExpenseSplit,
            SharedExpenseSplit.shared_expense_id == SharedExpense.id,
        )
        .where(
            or_(
                (SharedExpense.created_by_user_id == user_a)
                & (SharedExpenseSplit.user_id == user_b),
                (SharedExpense.created_by_user_id == user_b)
                & (SharedExpenseSplit.user_id == user_a),
            )
        )
        .order_by(SharedExpense.created_at.desc())
    )
    result = await session.execute(stmt)
    return [(e, s) for e, s in result.all()]


# ---------- Balance + settle ----------


@dataclass(frozen=True)
class BalancesByCurrency:
    """Signed net balance per currency between the viewer and one friend.

    Positive amount → the friend owes the viewer that much in that currency.
    Negative → the viewer owes the friend.
    """
    per_currency: dict[str, Decimal]


async def net_balance_with(
    session: AsyncSession, *, viewer_id: int, friend_id: int
) -> BalancesByCurrency:
    """Sum approved splits between the two users, grouped by currency.

    Only APPROVED splits count. Pending, disputed, and settled don't.
    """
    # Amount the friend owes the viewer.
    stmt_they_owe = (
        select(SharedExpense.currency, func.sum(SharedExpenseSplit.amount_owed))
        .join(
            SharedExpenseSplit,
            SharedExpenseSplit.shared_expense_id == SharedExpense.id,
        )
        .where(
            SharedExpense.created_by_user_id == viewer_id,
            SharedExpenseSplit.user_id == friend_id,
            SharedExpenseSplit.status == SplitStatus.APPROVED,
        )
        .group_by(SharedExpense.currency)
    )
    # Amount the viewer owes the friend.
    stmt_i_owe = (
        select(SharedExpense.currency, func.sum(SharedExpenseSplit.amount_owed))
        .join(
            SharedExpenseSplit,
            SharedExpenseSplit.shared_expense_id == SharedExpense.id,
        )
        .where(
            SharedExpense.created_by_user_id == friend_id,
            SharedExpenseSplit.user_id == viewer_id,
            SharedExpenseSplit.status == SplitStatus.APPROVED,
        )
        .group_by(SharedExpense.currency)
    )

    per_currency: dict[str, Decimal] = {}
    for row in (await session.execute(stmt_they_owe)).all():
        per_currency[row[0]] = per_currency.get(row[0], Decimal(0)) + Decimal(str(row[1]))
    for row in (await session.execute(stmt_i_owe)).all():
        per_currency[row[0]] = per_currency.get(row[0], Decimal(0)) - Decimal(str(row[1]))

    # Trim zeros so the UI doesn't show "0.00 EUR" for a currency that cancelled out.
    return BalancesByCurrency(
        per_currency={c: v for c, v in per_currency.items() if v != 0}
    )


async def settle_with_friend(
    session: AsyncSession, *, viewer_id: int, friend_id: int
) -> int:
    """Mark every APPROVED split between viewer and friend (in either
    direction) as SETTLED. Returns the number of splits updated."""
    stmt = (
        select(SharedExpenseSplit, SharedExpense)
        .join(
            SharedExpense,
            SharedExpense.id == SharedExpenseSplit.shared_expense_id,
        )
        .where(
            SharedExpenseSplit.status == SplitStatus.APPROVED,
            or_(
                (SharedExpense.created_by_user_id == viewer_id)
                & (SharedExpenseSplit.user_id == friend_id),
                (SharedExpense.created_by_user_id == friend_id)
                & (SharedExpenseSplit.user_id == viewer_id),
            ),
        )
    )
    rows = list((await session.execute(stmt)).all())

    now = datetime.now(UTC)
    changed_expense_ids: set[uuid.UUID] = set()
    for split, expense in rows:
        split.status = SplitStatus.SETTLED
        split.settled_at = now
        session.add(split)
        changed_expense_ids.add(expense.id)

    for expense_id in changed_expense_ids:
        await _recompute_expense_status(session, expense_id)

    await session.flush()
    return len(rows)
