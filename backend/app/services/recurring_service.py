"""Recurring templates: CRUD, tick, confirm/skip an occurrence."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

from dateutil.relativedelta import relativedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category, CategoryType
from app.models.frequency import Frequency
from app.models.recurring import (
    OccurrenceStatus,
    RecurringOccurrence,
    RecurringTemplate,
)
from app.models.transaction import Transaction, TransactionSource, TransactionType
from app.services.transaction_service import create_transaction


class RecurringError(ValueError):
    """User-facing error."""


# ---------- CRUD ----------


async def create_template(
    session: AsyncSession,
    *,
    user_id: int,
    account_id: uuid.UUID,
    category_id: uuid.UUID,
    amount,
    description: str,
    frequency: Frequency,
    next_due_date: date,
) -> RecurringTemplate:
    description = description.strip()
    if not description:
        raise RecurringError("description is required")
    if amount <= 0:
        raise RecurringError("amount must be positive")

    # Derive the currency from the account so the tick can create the tx
    # against the same denomination without a second lookup.
    from app.services.account_service import get_account

    account = await get_account(session, account_id=account_id, user_id=user_id)
    if account is None:
        raise RecurringError("account not found")

    stmt = select(Category.id).where(
        Category.id == category_id, Category.user_id == user_id
    )
    if (await session.execute(stmt)).scalar_one_or_none() is None:
        raise RecurringError("category not found")

    template = RecurringTemplate(
        user_id=user_id,
        account_id=account_id,
        category_id=category_id,
        amount=amount,
        currency=account.currency,
        description=description,
        frequency=frequency,
        next_due_date=next_due_date,
    )
    session.add(template)
    await session.flush()
    return template


async def get_template(
    session: AsyncSession, *, template_id: uuid.UUID, user_id: int
) -> RecurringTemplate | None:
    t = await session.get(RecurringTemplate, template_id)
    if t is None or t.user_id != user_id:
        return None
    return t


async def list_templates(
    session: AsyncSession, user_id: int, *, include_inactive: bool = False
) -> list[RecurringTemplate]:
    stmt = select(RecurringTemplate).where(RecurringTemplate.user_id == user_id)
    if not include_inactive:
        stmt = stmt.where(RecurringTemplate.is_active.is_(True))
    stmt = stmt.order_by(RecurringTemplate.next_due_date)
    return list((await session.execute(stmt)).scalars().all())


async def delete_template(session: AsyncSession, template: RecurringTemplate) -> None:
    await session.delete(template)
    await session.flush()


# ---------- Frequency math ----------


def next_due(current: date, frequency: Frequency) -> date:
    if frequency == Frequency.DAILY:
        return current + timedelta(days=1)
    if frequency == Frequency.WEEKLY:
        return current + timedelta(weeks=1)
    if frequency == Frequency.MONTHLY:
        return current + relativedelta(months=1)
    if frequency == Frequency.YEARLY:
        return current + relativedelta(years=1)
    raise RecurringError(f"unknown frequency: {frequency}")


# ---------- Tick + occurrence lifecycle ----------


async def list_due_templates(
    session: AsyncSession, *, today: date
) -> list[RecurringTemplate]:
    stmt = (
        select(RecurringTemplate)
        .where(
            RecurringTemplate.is_active.is_(True),
            RecurringTemplate.next_due_date <= today,
        )
        .order_by(RecurringTemplate.next_due_date)
    )
    return list((await session.execute(stmt)).scalars().all())


async def get_pending_occurrence(
    session: AsyncSession, *, template_id: uuid.UUID, due_date: date
) -> RecurringOccurrence | None:
    stmt = select(RecurringOccurrence).where(
        RecurringOccurrence.template_id == template_id,
        RecurringOccurrence.due_date == due_date,
    )
    return (await session.execute(stmt)).scalars().first()


async def upsert_pending_occurrence(
    session: AsyncSession, *, template: RecurringTemplate
) -> tuple[RecurringOccurrence, bool]:
    """Return (occurrence, created). If a pending row already exists for this
    template's current next_due_date, we hand it back untouched — the tick
    should only nudge the user once per due date."""
    existing = await get_pending_occurrence(
        session, template_id=template.id, due_date=template.next_due_date
    )
    if existing is not None:
        return existing, False

    occurrence = RecurringOccurrence(
        template_id=template.id,
        due_date=template.next_due_date,
        status=OccurrenceStatus.PENDING,
    )
    session.add(occurrence)
    await session.flush()
    return occurrence, True


async def _category_tx_type(
    session: AsyncSession, category_id: uuid.UUID
) -> TransactionType:
    category = await session.get(Category, category_id)
    if category is None or category.type == CategoryType.EXPENSE:
        return TransactionType.EXPENSE
    return TransactionType.INCOME


async def confirm_occurrence(
    session: AsyncSession, occurrence: RecurringOccurrence
) -> tuple[RecurringOccurrence, Transaction]:
    """Log the transaction from the template, advance next_due_date, mark done."""
    if occurrence.status != OccurrenceStatus.PENDING:
        raise RecurringError("occurrence already resolved")

    template = await session.get(RecurringTemplate, occurrence.template_id)
    if template is None:
        raise RecurringError("template gone")

    tx_type = await _category_tx_type(session, template.category_id)
    # Timestamp the tx at the start of the due date (local-ish) — the
    # occurred_at column is a tz-aware datetime, so we pin midnight UTC.
    occurred_at = datetime.combine(
        template.next_due_date, datetime.min.time(), tzinfo=UTC
    )

    tx = await create_transaction(
        session,
        user_id=template.user_id,
        type=tx_type,
        account_id=template.account_id,
        amount=template.amount,
        occurred_at=occurred_at,
        category_id=template.category_id,
        description=template.description,
        source=TransactionSource.RECURRING,
    )

    occurrence.status = OccurrenceStatus.CONFIRMED
    occurrence.confirmed_transaction_id = tx.id
    template.next_due_date = next_due(template.next_due_date, template.frequency)
    session.add(occurrence)
    session.add(template)
    await session.flush()
    return occurrence, tx


async def skip_occurrence(
    session: AsyncSession, occurrence: RecurringOccurrence
) -> RecurringOccurrence:
    if occurrence.status != OccurrenceStatus.PENDING:
        raise RecurringError("occurrence already resolved")
    template = await session.get(RecurringTemplate, occurrence.template_id)
    if template is None:
        raise RecurringError("template gone")

    occurrence.status = OccurrenceStatus.SKIPPED
    template.next_due_date = next_due(template.next_due_date, template.frequency)
    session.add(occurrence)
    session.add(template)
    await session.flush()
    return occurrence
