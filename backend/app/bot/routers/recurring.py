"""Callback handlers for the recurring "log it / skip" prompts."""

from __future__ import annotations

import logging
import uuid

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.core.db import session_scope
from app.i18n import get_i18n
from app.models.recurring import RecurringOccurrence
from app.models.user import User
from app.services.recurring_service import (
    RecurringError,
    confirm_occurrence,
    skip_occurrence,
)

log = logging.getLogger(__name__)
router = Router(name="recurring")


@router.callback_query(F.data.startswith("rec:"))
async def handle_recurring(cb: CallbackQuery) -> None:
    if cb.from_user is None or not cb.data:
        await cb.answer()
        return

    parts = cb.data.split(":", 2)
    if len(parts) != 3:
        await cb.answer()
        return
    _, action, occurrence_id = parts

    try:
        oid = uuid.UUID(occurrence_id)
    except (ValueError, TypeError):
        await cb.answer()
        return

    i18n = get_i18n()

    async with session_scope() as session:
        user = await session.get(User, cb.from_user.id)
        lang = user.language_code if user else "en"
        occurrence = await session.get(RecurringOccurrence, oid)

        if occurrence is None:
            await cb.answer(i18n.t(lang, "recurring.gone"), show_alert=True)
            if cb.message:
                try:
                    await cb.message.edit_reply_markup(reply_markup=None)
                except Exception:
                    pass
            return

        try:
            if action == "confirm":
                await confirm_occurrence(session, occurrence)
                answer_key = "recurring.answered.confirmed"
                followup_key = "recurring.followup.confirmed"
            elif action == "skip":
                await skip_occurrence(session, occurrence)
                answer_key = "recurring.answered.skipped"
                followup_key = "recurring.followup.skipped"
            else:
                await cb.answer()
                return
        except RecurringError as exc:
            log.info("recurring action failed: %s", exc)
            await cb.answer(i18n.t(lang, "recurring.already_resolved"), show_alert=True)
            if cb.message:
                try:
                    await cb.message.edit_reply_markup(reply_markup=None)
                except Exception:
                    pass
            return

    await cb.answer(i18n.t(lang, answer_key))
    if cb.message:
        await cb.message.edit_reply_markup(reply_markup=None)
        await cb.message.answer(i18n.t(lang, followup_key))
