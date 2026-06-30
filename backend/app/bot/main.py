"""Bot entrypoint. Boots aiogram in long-polling mode."""

from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.bot.routers import start
from app.core.bootstrap import load_app_context
from app.core.config import get_settings
from app.core.logging import configure_logging

log = logging.getLogger(__name__)


async def run() -> int:
    settings = get_settings()
    configure_logging(settings.log_level)

    if not settings.telegram_bot_token:
        log.warning(
            "TELEGRAM_BOT_TOKEN is not set — bot will not start. "
            "Edit .env, set the token from @BotFather, then: "
            "`docker compose up -d bot`"
        )
        # Exit 0 so the on-failure restart policy doesn't loop.
        return 0

    # Fail fast if any YAML config is malformed.
    load_app_context()

    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(start.router)

    me = await bot.get_me()
    log.info("bot online: @%s (id=%s)", me.username, me.id)

    # Drop any pending updates so we don't reprocess old ones after a restart.
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
