"""/start — greet the user and either open the Mini App or welcome them back."""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)

from app.core.config import get_settings
from app.core.db import session_scope
from app.i18n import get_i18n
from app.services.user_service import get_or_create_user

log = logging.getLogger(__name__)
router = Router(name="start")


def _open_app_keyboard(label: str, miniapp_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, web_app=WebAppInfo(url=miniapp_url))]
        ]
    )


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    tg_user = message.from_user
    if tg_user is None:
        return

    async with session_scope() as session:
        user, created = await get_or_create_user(
            session,
            telegram_id=tg_user.id,
            username=tg_user.username,
            display_name=tg_user.full_name or tg_user.username or str(tg_user.id),
            language_hint=tg_user.language_code,
        )
        lang = user.language_code
        display_name = user.display_name
        onboarded = user.onboarding_completed

    if created:
        log.info("new user registered: %s (%s)", tg_user.id, tg_user.username)

    i18n = get_i18n()
    settings = get_settings()
    miniapp_url = settings.miniapp_url.strip()

    if onboarded:
        await message.answer(i18n.t(lang, "start.welcome_back", name=display_name))
        return

    key = "start.welcome_new" if created else "start.welcome_unfinished"
    text = i18n.t(lang, key, name=display_name)

    if not miniapp_url:
        await message.answer(text)
        await message.answer(i18n.t(lang, "start.miniapp_not_configured"))
        return

    await message.answer(
        text,
        reply_markup=_open_app_keyboard(i18n.t(lang, "common.open_app"), miniapp_url),
    )
