"""split:approve / split:dispute callback handlers."""

from __future__ import annotations

import logging
import uuid

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import CallbackQuery

from app.core.db import session_scope
from app.i18n import get_i18n
from app.models.shared_expense import SharedExpense
from app.models.user import User
from app.services.shared_expense_service import (
    SharedExpenseError,
    approve_split,
    dispute_split,
    get_split,
)

log = logging.getLogger(__name__)
router = Router(name="shared_expenses")


@router.callback_query(F.data.startswith("split:"))
async def handle_split_action(cb: CallbackQuery) -> None:
    if cb.from_user is None or not cb.data:
        await cb.answer()
        return

    parts = cb.data.split(":", 2)
    if len(parts) != 3:
        await cb.answer()
        return
    _, action, split_id = parts

    try:
        sid = uuid.UUID(split_id)
    except (ValueError, TypeError):
        await cb.answer()
        return

    i18n = get_i18n()

    async with session_scope() as session:
        me = await session.get(User, cb.from_user.id)
        lang = me.language_code if me else "en"
        split = await get_split(session, sid)
        if split is None or me is None:
            await cb.answer(i18n.t(lang, "shared_expense.gone"), show_alert=True)
            if cb.message:
                try:
                    await cb.message.edit_reply_markup(reply_markup=None)
                except Exception:
                    pass
            return

        try:
            if action == "approve":
                await approve_split(session, split=split, actor=me)
                answer_key = "shared_expense.answered.approved"
                followup_key = "shared_expense.followup.approved"
            elif action == "dispute":
                await dispute_split(session, split=split, actor=me)
                answer_key = "shared_expense.answered.disputed"
                followup_key = "shared_expense.followup.disputed"
            else:
                await cb.answer()
                return
        except SharedExpenseError as exc:
            log.info("split action rejected: %s", exc)
            await cb.answer(
                i18n.t(lang, "shared_expense.action_failed"), show_alert=True
            )
            return

        expense = await session.get(SharedExpense, split.shared_expense_id)
        creator = (
            await session.get(User, expense.created_by_user_id) if expense else None
        )

    await cb.answer(i18n.t(lang, answer_key))
    if cb.message:
        await cb.message.edit_reply_markup(reply_markup=None)
        await cb.message.answer(
            i18n.t(
                lang,
                followup_key,
                description=expense.description if expense else "?",
            )
        )

    # Notify the creator on dispute so they can follow up.
    if action == "dispute" and creator is not None and expense is not None:
        try:
            await cb.bot.send_message(
                chat_id=creator.telegram_id,
                text=i18n.t(
                    creator.language_code,
                    "shared_expense.creator_disputed",
                    friend_name=me.display_name,
                    description=expense.description,
                ),
            )
        except (TelegramForbiddenError, TelegramBadRequest):
            pass
