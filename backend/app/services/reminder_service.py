"""Reminder CRUD + scheduler tick logic."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from dateutil.relativedelta import relativedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.frequency import Frequency
from app.models.reminder import Reminder, ReminderType


class ReminderError(ValueError):
    """User-facing input error."""


# ---------- CRUD ----------


async def create_reminder(
    session: AsyncSession,
    *,
    user_id: int,
    title: str,
    due_at: datetime,
    reminder_type: ReminderType = ReminderType.CUSTOM,
    description: str | None = None,
    repeat_frequency: Frequency | None = None,
) -> Reminder:
    title = title.strip()
    if not title:
        raise ReminderError("title is required")

    if due_at.tzinfo is None:
        due_at = due_at.replace(tzinfo=UTC)

    reminder = Reminder(
        user_id=user_id,
        title=title,
        description=description,
        reminder_type=reminder_type,
        due_at=due_at,
        repeat_frequency=repeat_frequency,
    )
    session.add(reminder)
    await session.flush()
    return reminder


async def get_reminder(
    session: AsyncSession, *, reminder_id: uuid.UUID, user_id: int
) -> Reminder | None:
    r = await session.get(Reminder, reminder_id)
    if r is None or r.user_id != user_id:
        return None
    return r


async def list_reminders(
    session: AsyncSession,
    user_id: int,
    *,
    include_inactive: bool = False,
) -> list[Reminder]:
    stmt = select(Reminder).where(Reminder.user_id == user_id)
    if not include_inactive:
        stmt = stmt.where(Reminder.is_active.is_(True))
    stmt = stmt.order_by(Reminder.due_at)
    return list((await session.execute(stmt)).scalars().all())


async def delete_reminder(session: AsyncSession, reminder: Reminder) -> None:
    await session.delete(reminder)
    await session.flush()


_EDITABLE_FIELDS = {
    "title",
    "description",
    "due_at",
    "repeat_frequency",
    "is_active",
}


async def update_reminder(
    session: AsyncSession, *, reminder: Reminder, fields: dict
) -> Reminder:
    unknown = set(fields) - _EDITABLE_FIELDS
    if unknown:
        raise ReminderError(f"cannot edit {sorted(unknown)}")
    for key, value in fields.items():
        if key == "due_at" and value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        setattr(reminder, key, value)
    session.add(reminder)
    await session.flush()
    return reminder


# ---------- Tick / advance ----------


def next_due(current: datetime, frequency: Frequency) -> datetime:
    if frequency == Frequency.DAILY:
        return current + timedelta(days=1)
    if frequency == Frequency.WEEKLY:
        return current + timedelta(weeks=1)
    if frequency == Frequency.MONTHLY:
        return current + relativedelta(months=1)
    if frequency == Frequency.YEARLY:
        return current + relativedelta(years=1)
    raise ReminderError(f"unknown frequency: {frequency}")


async def list_due(session: AsyncSession, *, now: datetime) -> list[Reminder]:
    """Reminders whose due_at has arrived and haven't been fired for this due."""
    stmt = (
        select(Reminder)
        .where(
            Reminder.is_active.is_(True),
            Reminder.due_at <= now,
        )
        .order_by(Reminder.due_at)
    )
    reminders = list((await session.execute(stmt)).scalars().all())
    # Filter out already-fired-for-this-due (last_fired_at >= due_at).
    return [
        r
        for r in reminders
        if r.last_fired_at is None or r.last_fired_at < r.due_at
    ]


async def mark_fired(
    session: AsyncSession, *, reminder: Reminder, now: datetime
) -> Reminder:
    """After sending, advance repeating reminders or deactivate one-shots.

    For a repeating reminder that missed many periods (bot was down), advance
    until the next due_at is in the future.
    """
    reminder.last_fired_at = now
    if reminder.repeat_frequency is None:
        reminder.is_active = False
    else:
        new_due = next_due(reminder.due_at, reminder.repeat_frequency)
        while new_due <= now:
            new_due = next_due(new_due, reminder.repeat_frequency)
        reminder.due_at = new_due
    session.add(reminder)
    await session.flush()
    return reminder
