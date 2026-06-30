"""Account CRUD."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account, AccountType


async def create_account(
    session: AsyncSession,
    *,
    user_id: int,
    name: str,
    type: AccountType,
    currency: str,
    icon: str = "fa-wallet",
    is_default: bool = False,
    is_default_income: bool = False,
) -> Account:
    account = Account(
        user_id=user_id,
        name=name,
        type=type,
        currency=currency,
        icon=icon,
        is_default=is_default,
        is_default_income=is_default_income,
    )
    session.add(account)
    await session.flush()
    return account


async def list_accounts(
    session: AsyncSession, user_id: int, *, include_archived: bool = False
) -> list[Account]:
    stmt = select(Account).where(Account.user_id == user_id)
    if not include_archived:
        stmt = stmt.where(Account.is_archived.is_(False))
    stmt = stmt.order_by(Account.created_at)
    result = await session.execute(stmt)
    return list(result.scalars().all())
