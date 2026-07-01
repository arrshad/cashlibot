"""Free-text messages route to the AI agent."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.ai.agent import run_agent
from app.ai.context import AgentContext
from app.ai.preview_store import load_preview
from app.ai.provider import AIUnavailableError
from app.core.bootstrap import load_app_context
from app.core.config import get_settings
from app.core.db import session_scope
from app.core.exceptions import InsufficientCreditsError
from app.core.redis import make_redis
from app.i18n import get_i18n
from app.models.credit import CreditReason
from app.models.user import User
from app.services.account_service import list_accounts
from app.services.category_service import list_categories
from app.services.credit_service import deduct_credits

log = logging.getLogger(__name__)
router = Router(name="chat")


# Anything that isn't a command falls through here.
@router.message(F.text & ~F.text.startswith("/"))
async def handle_free_text(message: Message) -> None:
    if not message.text or not message.from_user:
        return

    tg_user = message.from_user
    i18n = get_i18n()
    app_ctx = load_app_context()
    settings = get_settings()

    # Phase 1: gate on onboarding + credits, and charge for the call up-front.
    async with session_scope() as session:
        user = await session.get(User, tg_user.id)
        if user is None:
            await message.answer(i18n.t("en", "chat.not_registered"))
            return
        lang = user.language_code
        if not user.onboarding_completed:
            await message.answer(i18n.t(lang, "chat.not_onboarded"))
            return

        try:
            await deduct_credits(
                session,
                user=user,
                amount=app_ctx.app.credits.ai_agent_call_cost,
                reason=CreditReason.AI_USAGE,
            )
        except InsufficientCreditsError:
            await message.answer(i18n.t(lang, "chat.no_credits"))
            return

    # Phase 2: run the agent. Redis reused for the whole handler.
    redis = make_redis()
    try:
        async with session_scope() as session:
            user = await session.get(User, tg_user.id)
            if user is None:
                return  # shouldn't happen — we just charged them
            accounts = await list_accounts(session, tg_user.id)
            categories = await list_categories(session, user_id=tg_user.id)
            ctx = AgentContext(
                user=user,
                session=session,
                redis=redis,
                accounts=accounts,
                categories=categories,
            )
            try:
                result = await run_agent(
                    ctx,
                    user_message=message.text,
                    ai_config=app_ctx.ai_providers,
                    settings=settings,
                )
            except AIUnavailableError as exc:
                log.warning("AI unavailable: %s", exc)
                await message.answer(i18n.t(lang, "chat.ai_unavailable"))
                return
            except Exception:
                log.exception("agent crashed for user %s", tg_user.id)
                await message.answer(i18n.t(lang, "chat.ai_error"))
                return

        # Phase 3: render — either plain text, or the preview + confirm buttons.
        if not result.preview_ids:
            await message.answer(result.text or i18n.t(lang, "chat.ai_empty"))
            return

        preview_id = result.preview_ids[0]
        preview = await load_preview(redis, tg_user.id, preview_id)
        if preview is None:
            # Preview vanished between staging and rendering — degrade gracefully.
            await message.answer(result.text or i18n.t(lang, "chat.ai_empty"))
            return

        summary = preview.summary_fa if lang == "fa" else preview.summary_en
        agent_text = result.text.strip() if result.text else ""
        body = f"{agent_text}\n\n{summary}" if agent_text else summary
        await message.answer(
            body,
            reply_markup=_confirm_keyboard(lang, preview_id, i18n),
        )
    finally:
        await redis.aclose()


def _confirm_keyboard(lang: str, preview_id: str, i18n) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.t(lang, "chat.preview.confirm"),
                    callback_data=f"preview:confirm:{preview_id}",
                ),
                InlineKeyboardButton(
                    text=i18n.t(lang, "chat.preview.cancel"),
                    callback_data=f"preview:cancel:{preview_id}",
                ),
            ]
        ]
    )
