"""Account CRUD."""

from __future__ import annotations

import uuid

from sqlalchemy import select, update
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
    color: str | None = None,
    is_default: bool = False,
    is_default_income: bool = False,
) -> Account:
    if is_default:
        await _clear_flag(session, user_id, "is_default")
    if is_default_income:
        await _clear_flag(session, user_id, "is_default_income")

    account = Account(
        user_id=user_id,
        name=name,
        type=type,
        currency=currency,
        icon=icon,
        color=color,
        is_default=is_default,
        is_default_income=is_default_income,
    )
    session.add(account)
    await session.flush()
    return account


async def get_account(
    session: AsyncSession, *, account_id: uuid.UUID, user_id: int
) -> Account | None:
    """Look up an account by id, ensuring it belongs to this user."""
    account = await session.get(Account, account_id)
    if account is None or account.user_id != user_id:
        return None
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


# Fields users can patch through the API. Balance is computed from transactions
# and currency can't change once the account exists.
_EDITABLE_FIELDS = {"name", "icon", "color", "is_default", "is_default_income"}


async def update_account(
    session: AsyncSession,
    *,
    account: Account,
    fields: dict[str, object],
) -> Account:
    for key in fields:
        if key not in _EDITABLE_FIELDS:
            raise ValueError(f"field '{key}' is not editable")

    if fields.get("is_default") is True:
        await _clear_flag(session, account.user_id, "is_default", except_id=account.id)
    if fields.get("is_default_income") is True:
        await _clear_flag(
            session, account.user_id, "is_default_income", except_id=account.id
        )

    for key, value in fields.items():
        setattr(account, key, value)
    session.add(account)
    await session.flush()
    return account


async def archive_account(session: AsyncSession, account: Account) -> Account:
    account.is_archived = True
    # Archiving the default account vacates the slot; the next create or
    # update can claim it.
    account.is_default = False
    account.is_default_income = False
    session.add(account)
    await session.flush()
    return account


async def _clear_flag(
    session: AsyncSession,
    user_id: int,
    field: str,
    *,
    except_id: uuid.UUID | None = None,
) -> None:
    """Set `field=False` on every account of this user (optionally skipping one)."""
    stmt = update(Account).where(Account.user_id == user_id, getattr(Account, field).is_(True))
    if except_id is not None:
        stmt = stmt.where(Account.id != except_id)
    await session.execute(stmt.values({field: False}))
