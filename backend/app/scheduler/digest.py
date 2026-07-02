"""Scheduler job: DM each opted-in user their weekly digest at their preferred hour."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from sqlalchemy import select

from app.core.db import session_scope
from app.models.user import User
from app.services.digest_service import build_digest

log = logging.getLogger(__name__)

# 15 min: fine-grained enough to hit each hour-boundary once, coarse enough
# that we don't hammer the DB. Combined with the >= 6 days dedupe, users get
# exactly one digest per week even if the tick fires four times inside the
# matching hour.
TICK_INTERVAL_SECONDS = 15 * 60

# Never send more than one digest per 6 days per user, even if the scheduler
# restarts or the user changes prefs mid-week.
MIN_INTERVAL = timedelta(days=6)


def _tz(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def _is_due(user: User, now_utc: datetime) -> bool:
    if not user.weekly_digest_enabled or not user.onboarding_completed:
        return False
    now_local = now_utc.astimezone(_tz(user.timezone))
    # Fire once per week when the user's local wall clock hits their preferred
    # day-of-week + hour. Minute is ignored so the 15-min tick still catches it.
    if now_local.weekday() != user.weekly_digest_dow:
        return False
    if now_local.hour != user.weekly_digest_hour:
        return False
    if user.last_weekly_digest_at is not None:
        if now_utc - user.last_weekly_digest_at < MIN_INTERVAL:
            return False
    return True


async def tick_digests(bot: Bot) -> None:
    """Send digests to every user whose local (dow, hour) matches right now."""
    now_utc = datetime.now(UTC)

    async with session_scope() as session:
        stmt = select(User).where(
            User.weekly_digest_enabled.is_(True),
            User.onboarding_completed.is_(True),
        )
        candidates = list((await session.execute(stmt)).scalars().all())

        due = [u for u in candidates if _is_due(u, now_utc)]
        if not due:
            return
        log.info("weekly digest: %d user(s) due at %s", len(due), now_utc.isoformat())

        for user in due:
            try:
                payload = await build_digest(session, user=user)
            except Exception:
                log.exception("digest: build failed for user %s", user.telegram_id)
                continue

            if payload is None:
                # No activity this week — mark as "sent" anyway so we don't
                # rebuild the same empty digest every tick for the rest of the
                # hour. The user will get one next week if they log something.
                user.last_weekly_digest_at = now_utc
                session.add(user)
                continue

            try:
                await bot.send_message(chat_id=user.telegram_id, text=payload.text)
            except (TelegramForbiddenError, TelegramBadRequest) as exc:
                log.warning(
                    "digest: send to %s failed (%s); disabling their digest",
                    user.telegram_id,
                    exc,
                )
                # User blocked the bot or their chat is gone. Stop pestering.
                user.weekly_digest_enabled = False
                session.add(user)
                continue
            except Exception:
                log.exception(
                    "digest: unexpected send error for user %s", user.telegram_id
                )
                continue

            user.last_weekly_digest_at = now_utc
            session.add(user)
