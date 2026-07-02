"""Bot entrypoint. Boots aiogram in long-polling mode."""

from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.bot.routers import chat, payments, preview, recurring, start
from app.core.bootstrap import load_app_context
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.scheduler.recurring import (
    TICK_INTERVAL_SECONDS as RECURRING_TICK_SECONDS,
    tick_recurring,
)
from app.scheduler.reminders import TICK_INTERVAL_SECONDS, tick_reminders

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
    # Order matters: command + callback handlers first, then the free-text
    # catch-all last so commands don't fall through into the AI.
    dp.include_router(start.router)
    dp.include_router(payments.router)
    dp.include_router(preview.router)
    dp.include_router(recurring.router)
    dp.include_router(chat.router)

    me = await bot.get_me()
    log.info("bot online: @%s (id=%s)", me.username, me.id)

    # Drop any pending updates so we don't reprocess old ones after a restart.
    await bot.delete_webhook(drop_pending_updates=True)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        tick_reminders,
        IntervalTrigger(seconds=TICK_INTERVAL_SECONDS),
        args=[bot],
        id="reminders_tick",
        coalesce=True,
        max_instances=1,
        replace_existing=True,
    )
    scheduler.add_job(
        tick_recurring,
        IntervalTrigger(seconds=RECURRING_TICK_SECONDS),
        args=[bot],
        id="recurring_tick",
        coalesce=True,
        max_instances=1,
        replace_existing=True,
    )
    scheduler.start()
    log.info(
        "scheduler started (reminders every %ds, recurring every %ds)",
        TICK_INTERVAL_SECONDS,
        RECURRING_TICK_SECONDS,
    )

    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
