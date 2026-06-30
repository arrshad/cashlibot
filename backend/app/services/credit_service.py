"""Credit balance changes always go through this service.

Every change updates `User.credit_balance` AND inserts a `CreditTransaction`
row recording the delta, the reason, and the resulting balance. The two
writes happen in the same session so they share a transaction.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InsufficientCreditsError
from app.models.credit import CreditReason, CreditTransaction
from app.models.user import User


async def add_credits(
    session: AsyncSession,
    *,
    user: User,
    amount: int,
    reason: CreditReason,
    reference_id: str | None = None,
) -> CreditTransaction:
    """Grant credits to a user. `amount` must be positive."""
    if amount <= 0:
        raise ValueError("add_credits amount must be positive")
    return await _apply(session, user=user, delta=amount, reason=reason, reference_id=reference_id)


async def deduct_credits(
    session: AsyncSession,
    *,
    user: User,
    amount: int,
    reason: CreditReason,
    reference_id: str | None = None,
) -> CreditTransaction:
    """Charge credits to a user. Raises InsufficientCreditsError if balance is too low."""
    if amount <= 0:
        raise ValueError("deduct_credits amount must be positive")
    if user.credit_balance < amount:
        raise InsufficientCreditsError(
            f"need {amount} credits, have {user.credit_balance}"
        )
    return await _apply(session, user=user, delta=-amount, reason=reason, reference_id=reference_id)


async def _apply(
    session: AsyncSession,
    *,
    user: User,
    delta: int,
    reason: CreditReason,
    reference_id: str | None,
) -> CreditTransaction:
    user.credit_balance = user.credit_balance + delta
    session.add(user)

    entry = CreditTransaction(
        user_id=user.telegram_id,
        change_amount=delta,
        balance_after=user.credit_balance,
        reason=reason,
        reference_id=reference_id,
    )
    session.add(entry)
    await session.flush()
    return entry
