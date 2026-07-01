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
from app.services.budget_service import ThresholdCrossing, check_after_expense
from app.services.categorization_service import upsert_rule
from app.services.category_service import list_categories
from app.services.gamification_service import (
    BadgeEarned,
    GamificationEvent,
    LevelUp,
    on_transaction_created,
)
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
        crossing: ThresholdCrossing | None = None
        category_name = ""
        events: list[GamificationEvent] = []
        try:
            async with session_scope() as session:
                crossing, category_name, events = await _create_from_preview(
                    session,
                    preview,
                    cb.message.message_id if cb.message else None,
                    user_timezone=user.timezone if user else "UTC",
                )
        except TransactionError as exc:
            log.warning("confirm failed: %s", exc)
            await cb.answer(i18n.t(lang, "chat.preview.failed"), show_alert=True)
            return

        await discard_preview(redis, cb.from_user.id, preview_id)
        await cb.answer(i18n.t(lang, "chat.preview.confirmed_short"))
        if cb.message:
            await cb.message.edit_reply_markup(reply_markup=None)
            await cb.message.answer(i18n.t(lang, "chat.preview.confirmed"))
            if crossing is not None:
                await cb.message.answer(
                    _format_threshold(lang, i18n, crossing, category_name)
                )
            for line in _format_gamification(lang, i18n, events):
                await cb.message.answer(line)
    finally:
        await redis.aclose()


async def _create_from_preview(
    session,
    preview: TransactionPreview,
    reply_to_message_id: int | None,
    *,
    user_timezone: str,
) -> tuple[ThresholdCrossing | None, str, list[GamificationEvent]]:
    """Create the transaction, upsert rule, and return budget crossing + gamification events."""
    tx_type = TransactionType(preview.type)
    category_uuid = uuid.UUID(preview.category_id) if preview.category_id else None

    tx = await create_transaction(
        session,
        user_id=preview.user_id,
        type=tx_type,
        account_id=uuid.UUID(preview.account_id),
        amount=Decimal(preview.amount),
        occurred_at=datetime.fromisoformat(preview.occurred_at_iso),
        to_account_id=uuid.UUID(preview.to_account_id) if preview.to_account_id else None,
        category_id=category_uuid,
        merchant=preview.merchant,
        description=preview.description,
        source=TransactionSource.AI_PARSED,
        raw_input_text=preview.raw_input_text,
        reply_to_message_id=reply_to_message_id,
    )

    # If the confirmed transaction had both a merchant and a category, remember
    # that pairing so the AI can auto-categorize this merchant next time.
    if preview.merchant and category_uuid is not None:
        try:
            await upsert_rule(
                session,
                user_id=preview.user_id,
                keyword=preview.merchant,
                category_id=category_uuid,
            )
        except ValueError:
            pass

    # Budget threshold check — only expenses count against budgets.
    crossing: ThresholdCrossing | None = None
    category_display = ""
    if tx_type == TransactionType.EXPENSE:
        crossing = await check_after_expense(
            session,
            user_id=preview.user_id,
            category_id=category_uuid,
            added_amount=Decimal(preview.amount),
            tz_name=user_timezone,
        )
        if crossing is not None:
            cats = await list_categories(session, user_id=preview.user_id)
            for c in cats:
                if c.id == crossing.budget.category_id:
                    category_display = c.name_en or c.name
                    break

    # Gamification — streaks, XP, badges, level ups.
    events = await on_transaction_created(
        session,
        user_id=preview.user_id,
        source=tx.source,
        tz_name=user_timezone,
    )

    return crossing, category_display, events


def _format_gamification(lang: str, i18n, events: list[GamificationEvent]) -> list[str]:
    lines: list[str] = []
    for event in events:
        if isinstance(event, BadgeEarned):
            name = (
                event.badge.name_fa
                if lang == "fa" and event.badge.name_fa
                else event.badge.name
            )
            desc = (
                event.badge.description_fa
                if lang == "fa" and event.badge.description_fa
                else event.badge.description
            )
            lines.append(
                i18n.t(lang, "gamification.badge_earned", name=name, description=desc)
            )
        elif isinstance(event, LevelUp):
            lines.append(
                i18n.t(
                    lang,
                    "gamification.level_up",
                    from_level=event.from_level,
                    to_level=event.to_level,
                    total_xp=event.total_xp,
                )
            )
    return lines


def _format_threshold(lang: str, i18n, crossing: ThresholdCrossing, category: str) -> str:
    ratio = (crossing.spent / crossing.limit) if crossing.limit > 0 else Decimal(0)
    key = (
        "budget.notify.exceeded"
        if crossing.level == "exceeded"
        else "budget.notify.warning"
    )
    return i18n.t(
        lang,
        key,
        category=category or "?",
        period=crossing.budget.period.value,
        spent=str(crossing.spent),
        limit=str(crossing.limit),
        currency=crossing.budget.currency,
        percent=int(ratio * 100),
    )
