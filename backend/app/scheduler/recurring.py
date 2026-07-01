"""Scheduler job: nudge users about due recurring templates."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.core.db import session_scope
from app.i18n import get_i18n
from app.models.user import User
from app.services.recurring_service import (
    list_due_templates,
    upsert_pending_occurrence,
)

log = logging.getLogger(__name__)

# 15-minute cadence is enough for daily-granularity recurring nudges — much
# longer would delay a fresh due-date notification, much shorter would burn
# DB cycles.
TICK_INTERVAL_SECONDS = 15 * 60


async def tick_recurring(bot: Bot) -> None:
    today = datetime.now(UTC).date()

    async with session_scope() as session:
        due_templates = await list_due_templates(session, today=today)
        if not due_templates:
            return
        log.info("nudging %d recurring template(s)", len(due_templates))

        for template in due_templates:
            occurrence, created = await upsert_pending_occurrence(
                session, template=template
            )
            if not created:
                # Already asked the user for this due date; wait for them.
                continue

            user = await session.get(User, template.user_id)
            if user is None:
                continue
            lang = user.language_code

            i18n = get_i18n()
            text = i18n.t(
                lang,
                "recurring.due_prompt",
                description=template.description,
                amount=str(template.amount),
                currency=template.currency,
            )
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=i18n.t(lang, "recurring.button.confirm"),
                            callback_data=f"rec:confirm:{occurrence.id}",
                        ),
                        InlineKeyboardButton(
                            text=i18n.t(lang, "recurring.button.skip"),
                            callback_data=f"rec:skip:{occurrence.id}",
                        ),
                    ]
                ]
            )

            try:
                await bot.send_message(
                    chat_id=template.user_id, text=text, reply_markup=keyboard
                )
            except (TelegramForbiddenError, TelegramBadRequest) as exc:
                # User blocked or chat gone — pause the template so we stop
                # hammering. They can re-enable in the Mini App if they come back.
                log.warning(
                    "recurring template %s: send failed (%s); deactivating",
                    template.id, exc,
                )
                template.is_active = False
                session.add(template)
            except Exception:
                log.exception("recurring template %s: unexpected send error", template.id)
