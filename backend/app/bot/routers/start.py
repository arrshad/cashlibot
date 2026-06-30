"""`/start` — creates the User row on first contact and replies with a welcome."""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.core.db import session_scope
from app.i18n import get_i18n
from app.models.user import User

log = logging.getLogger(__name__)
router = Router(name="start")


def _pick_initial_language(tg_lang: str | None) -> str:
    if tg_lang and tg_lang.lower().startswith("fa"):
        return "fa"
    return "en"


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    tg_user = message.from_user
    if tg_user is None:
        return

    async with session_scope() as session:
        user = await session.get(User, tg_user.id)
        if user is None:
            user = User(
                telegram_id=tg_user.id,
                username=tg_user.username,
                display_name=tg_user.full_name or tg_user.username or str(tg_user.id),
                language_code=_pick_initial_language(tg_user.language_code),
            )
            session.add(user)
            await session.flush()
            log.info("new user registered: %s (%s)", user.telegram_id, user.username)

        lang = user.language_code
        display_name = user.display_name

    text = get_i18n().t(lang, "start.welcome", name=display_name)
    await message.answer(text)
