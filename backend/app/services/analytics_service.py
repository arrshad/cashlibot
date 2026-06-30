"""Read-only analytics queries — all aggregations computed by SQL, never the LLM."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account


async def get_balances_by_currency(
    session: AsyncSession, user_id: int
) -> dict[str, Decimal]:
    """Sum each user's account balances grouped by currency. Archived excluded."""
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
