"""Scheduler job: check for due reminders and fire them."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from app.core.db import session_scope
from app.services.reminder_service import list_due, mark_fired

log = logging.getLogger(__name__)

TICK_INTERVAL_SECONDS = 60


async def tick_reminders(bot: Bot) -> None:
    """Fire any reminders whose due_at has arrived.

    Each fired reminder is sent as a bot chat message, then either advanced
    (repeating) or deactivated (one-shot). Send failures for a specific user
    are logged but don't stop the whole tick.
    """
    now = datetime.now(UTC)

    async with session_scope() as session:
        due = await list_due(session, now=now)
        if not due:
            return
        log.info("firing %d reminder(s) at %s", len(due), now.isoformat())

        for reminder in due:
            body = reminder.title
            if reminder.description:
                body = f"{reminder.title}\n\n{reminder.description}"
            try:
                await bot.send_message(chat_id=reminder.user_id, text=body)
            except (TelegramForbiddenError, TelegramBadRequest) as exc:
                # User blocked the bot or chat is gone. Deactivate quietly so
                # we stop hammering the API for this reminder.
                log.warning(
                    "reminder %s: send failed (%s); deactivating", reminder.id, exc
                )
                reminder.is_active = False
                session.add(reminder)
                continue
            except Exception:
                log.exception("reminder %s: unexpected send error", reminder.id)
                continue

            await mark_fired(session, reminder=reminder, now=now)
