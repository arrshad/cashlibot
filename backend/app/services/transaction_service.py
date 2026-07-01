"""Transactions: create/update/delete/list with atomic balance updates."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction, TransactionSource, TransactionType


class TransactionError(ValueError):
    """Invalid input — bad account/currency/amount/etc."""


# ---------- Public API ----------


async def create_transaction(
    session: AsyncSession,
    *,
    user_id: int,
    type: TransactionType,
    account_id: uuid.UUID,
    amount: Decimal,
    occurred_at: datetime,
    to_account_id: uuid.UUID | None = None,
    category_id: uuid.UUID | None = None,
    merchant: str | None = None,
    description: str | None = None,
    source: TransactionSource = TransactionSource.MANUAL,
    raw_input_text: str | None = None,
    reply_to_message_id: int | None = None,
    ai_confidence: float | None = None,
) -> Transaction:
    if amount <= 0:
        raise TransactionError("amount must be positive")

    account = await _load_owned_account(session, account_id, user_id)
    to_account = None
    if type == TransactionType.TRANSFER:
        if to_account_id is None:
            raise TransactionError("transfers need a to_account_id")
        if to_account_id == account_id:
            raise TransactionError("cannot transfer to the same account")
        to_account = await _load_owned_account(session, to_account_id, user_id)
        if to_account.currency != account.currency:
            # FX-less transfers only for now — log two txs instead.
            raise TransactionError(
                "transfer between different currencies isn't supported yet"
            )
    else:
        if to_account_id is not None:
            raise TransactionError("to_account_id only valid for transfers")

    if category_id is not None:
        await _ensure_owned_category(session, category_id, user_id)

    tx = Transaction(
        user_id=user_id,
        account_id=account_id,
        category_id=category_id,
        type=type,
        amount=amount,
        currency=account.currency,
        merchant=merchant,
        description=description,
        occurred_at=occurred_at,
        to_account_id=to_account_id,
        source=source,
        raw_input_text=raw_input_text,
        reply_to_message_id=reply_to_message_id,
        ai_confidence=ai_confidence,
    )
    session.add(tx)

    for target, delta in _effects(type, account_id, to_account_id, amount):
        await _bump_balance(session, target, delta)

    await session.flush()
    return tx


async def get_transaction(
    session: AsyncSession, *, transaction_id: uuid.UUID, user_id: int
) -> Transaction | None:
    tx = await session.get(Transaction, transaction_id)
    if tx is None or tx.user_id != user_id or tx.is_deleted:
        return None
    return tx


_EDITABLE_FIELDS = {
    "type",
    "account_id",
    "to_account_id",
    "category_id",
    "amount",
    "occurred_at",
    "merchant",
    "description",
}


async def update_transaction(
    session: AsyncSession,
    *,
    tx: Transaction,
    fields: dict[str, Any],
) -> Transaction:
    unknown = set(fields) - _EDITABLE_FIELDS
    if unknown:
        raise TransactionError(f"cannot edit {sorted(unknown)}")

    new_type = fields.get("type", tx.type)
    new_account_id = fields.get("account_id", tx.account_id)
    new_to_account_id = fields.get("to_account_id", tx.to_account_id)
    new_amount = fields.get("amount", tx.amount)
    new_category_id = fields.get("category_id", tx.category_id)

    if new_amount <= 0:
        raise TransactionError("amount must be positive")

    # Validate ownership + currency invariants for the *new* configuration.
    new_account = await _load_owned_account(session, new_account_id, tx.user_id)
    if new_type == TransactionType.TRANSFER:
        if new_to_account_id is None:
            raise TransactionError("transfers need a to_account_id")
        if new_to_account_id == new_account_id:
            raise TransactionError("cannot transfer to the same account")
        new_to_account = await _load_owned_account(
            session, new_to_account_id, tx.user_id
        )
        if new_to_account.currency != new_account.currency:
            raise TransactionError(
                "transfer between different currencies isn't supported yet"
            )
    else:
        new_to_account_id = None

    if new_category_id is not None:
        await _ensure_owned_category(session, new_category_id, tx.user_id)

    # 1. Reverse the old effect.
    for target, delta in _effects(tx.type, tx.account_id, tx.to_account_id, tx.amount):
        await _bump_balance(session, target, -delta)

    # 2. Apply the new effect.
    for target, delta in _effects(new_type, new_account_id, new_to_account_id, new_amount):
        await _bump_balance(session, target, delta)

    tx.type = new_type
    tx.account_id = new_account_id
    tx.to_account_id = new_to_account_id
    tx.amount = new_amount
    tx.category_id = new_category_id
    tx.currency = new_account.currency
    if "merchant" in fields:
        tx.merchant = fields["merchant"]
    if "description" in fields:
        tx.description = fields["description"]
    if "occurred_at" in fields:
        tx.occurred_at = fields["occurred_at"]
    tx.updated_at = datetime.now(UTC)

    session.add(tx)
    await session.flush()
    return tx


async def delete_transaction(session: AsyncSession, tx: Transaction) -> Transaction:
    """Soft-delete: reverse balances, mark row deleted, keep for audit."""
    for target, delta in _effects(tx.type, tx.account_id, tx.to_account_id, tx.amount):
        await _bump_balance(session, target, -delta)
    tx.is_deleted = True
    tx.updated_at = datetime.now(UTC)
    session.add(tx)
    await session.flush()
    return tx


async def list_transactions(
    session: AsyncSession,
    *,
    user_id: int,
    account_id: uuid.UUID | None = None,
    category_id: uuid.UUID | None = None,
    type: TransactionType | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Transaction]:
    stmt = select(Transaction).where(
        Transaction.user_id == user_id,
        Transaction.is_deleted.is_(False),
    )
    if account_id is not None:
        stmt = stmt.where(
            (Transaction.account_id == account_id)
            | (Transaction.to_account_id == account_id)
        )
    if category_id is not None:
        stmt = stmt.where(Transaction.category_id == category_id)
    if type is not None:
        stmt = stmt.where(Transaction.type == type)
    if start is not None:
        stmt = stmt.where(Transaction.occurred_at >= start)
    if end is not None:
        stmt = stmt.where(Transaction.occurred_at <= end)

    stmt = stmt.order_by(Transaction.occurred_at.desc()).limit(limit).offset(offset)
    result = await session.execute(stmt)
    return list(result.scalars().all())


# ---------- Internals ----------


def _effects(
    type: TransactionType,
    account_id: uuid.UUID,
    to_account_id: uuid.UUID | None,
    amount: Decimal,
) -> list[tuple[uuid.UUID, Decimal]]:
    """List of (account_id, signed_delta) to apply."""
    if type == TransactionType.INCOME:
        return [(account_id, amount)]
    if type == TransactionType.EXPENSE:
        return [(account_id, -amount)]
    if type == TransactionType.TRANSFER:
        assert to_account_id is not None
        return [(account_id, -amount), (to_account_id, amount)]
    raise TransactionError(f"unknown transaction type: {type}")


async def _bump_balance(
    session: AsyncSession, account_id: uuid.UUID, delta: Decimal
) -> None:
    """Atomically adjust `current_balance` by `delta` for one account."""
    await session.execute(
        update(Account)
        .where(Account.id == account_id)
        .values(current_balance=Account.current_balance + delta)
    )


async def _load_owned_account(
    session: AsyncSession, account_id: uuid.UUID, user_id: int
) -> Account:
    account = await session.get(Account, account_id)
    if account is None or account.user_id != user_id:
        raise TransactionError(f"account {account_id} not found")
    if account.is_archived:
        raise TransactionError("account is archived")
    return account


async def _ensure_owned_category(
    session: AsyncSession, category_id: uuid.UUID, user_id: int
) -> None:
    stmt = select(Category.id).where(
        and_(Category.id == category_id, Category.user_id == user_id)
    )
    if (await session.execute(stmt)).scalar_one_or_none() is None:
        raise TransactionError(f"category {category_id} not found")
