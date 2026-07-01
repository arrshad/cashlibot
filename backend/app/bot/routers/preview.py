"""Callback handlers for the AI transaction previews."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from decimal import Decimal

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.ai.preview_store import (
    TransactionPreview,
    discard_preview,
    load_preview,
)
from app.core.db import session_scope
from app.core.redis import make_redis
from app.i18n import get_i18n
from app.models.transaction import TransactionSource, TransactionType
from app.models.user import User
from app.services.categorization_service import upsert_rule
from app.services.transaction_service import (
    TransactionError,
    create_transaction,
)

log = logging.getLogger(__name__)
router = Router(name="preview")


@router.callback_query(F.data.startswith("preview:"))
async def handle_preview_action(cb: CallbackQuery) -> None:
    if cb.from_user is None or not cb.data:
        await cb.answer()
        return

    parts = cb.data.split(":", 2)
    if len(parts) != 3:
        await cb.answer()
        return
    _, action, preview_id = parts

    i18n = get_i18n()
    redis = make_redis()
    try:
        async with session_scope() as session:
            user = await session.get(User, cb.from_user.id)
        lang = user.language_code if user else "en"

        preview = await load_preview(redis, cb.from_user.id, preview_id)
        if preview is None:
            await cb.answer(i18n.t(lang, "chat.preview.expired"), show_alert=True)
            if cb.message:
                try:
                    await cb.message.edit_reply_markup(reply_markup=None)
                except Exception:
                    pass
            return

        if action == "cancel":
            await discard_preview(redis, cb.from_user.id, preview_id)
            await cb.answer(i18n.t(lang, "chat.preview.cancelled_short"))
            if cb.message:
                await cb.message.edit_reply_markup(reply_markup=None)
                await cb.message.answer(i18n.t(lang, "chat.preview.cancelled"))
            return

        if action != "confirm":
            await cb.answer()
            return

        # Confirm: create the transaction, then clean up the preview.
        try:
            async with session_scope() as session:
                await _create_from_preview(session, preview, cb.message.message_id if cb.message else None)
        except TransactionError as exc:
            log.warning("confirm failed: %s", exc)
            await cb.answer(i18n.t(lang, "chat.preview.failed"), show_alert=True)
            return

        await discard_preview(redis, cb.from_user.id, preview_id)
        await cb.answer(i18n.t(lang, "chat.preview.confirmed_short"))
        if cb.message:
            await cb.message.edit_reply_markup(reply_markup=None)
            await cb.message.answer(i18n.t(lang, "chat.preview.confirmed"))
    finally:
        await redis.aclose()


async def _create_from_preview(
    session,
    preview: TransactionPreview,
    reply_to_message_id: int | None,
) -> None:
    await create_transaction(
        session,
        user_id=preview.user_id,
        type=TransactionType(preview.type),
        account_id=uuid.UUID(preview.account_id),
        amount=Decimal(preview.amount),
        occurred_at=datetime.fromisoformat(preview.occurred_at_iso),
        to_account_id=uuid.UUID(preview.to_account_id) if preview.to_account_id else None,
        category_id=uuid.UUID(preview.category_id) if preview.category_id else None,
        merchant=preview.merchant,
        description=preview.description,
        source=TransactionSource.AI_PARSED,
        raw_input_text=preview.raw_input_text,
        reply_to_message_id=reply_to_message_id,
    )

    # If the confirmed transaction had both a merchant and a category, remember
    # that pairing so the AI can auto-categorize this merchant next time.
    if preview.merchant and preview.category_id:
        try:
            await upsert_rule(
                session,
                user_id=preview.user_id,
                keyword=preview.merchant,
                category_id=uuid.UUID(preview.category_id),
            )
        except ValueError:
            pass
