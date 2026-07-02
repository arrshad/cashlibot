"""/admin — mints a signed JWT for is_admin users and DMs the login URL."""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.core.admin_auth import InvalidAdminToken, create_admin_token
from app.core.config import get_settings
from app.core.db import session_scope
from app.i18n import get_i18n
from app.models.user import User

log = logging.getLogger(__name__)
router = Router(name="admin")


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    tg_user = message.from_user
    if tg_user is None:
        return

    i18n = get_i18n()
    async with session_scope() as session:
        user = await session.get(User, tg_user.id)

    lang = user.language_code if user else "en"

    if user is None or not user.is_admin:
        # Deliberately generic so we don't confirm/deny admin status to
        # someone probing for it.
        await message.answer(i18n.t(lang, "admin.not_available"))
        return

    settings = get_settings()
    try:
        token = create_admin_token(
            telegram_id=user.telegram_id, secret=settings.admin_jwt_secret
        )
    except InvalidAdminToken as exc:
        log.warning("admin token mint failed: %s", exc)
        await message.answer(i18n.t(lang, "admin.jwt_secret_missing"))
        return

    admin_url = settings.admin_url or "http://localhost:5174"
    link = f"{admin_url.rstrip('/')}/#token={token}"

    await message.answer(i18n.t(lang, "admin.link_ready", link=link))
