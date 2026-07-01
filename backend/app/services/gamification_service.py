"""Gamification: streaks, XP, level, and badges.

Everything here is computed from database state — no LLM involved.
Callers (transaction_service, savings_service, bot preview handler)
invoke `on_transaction_created` / `on_savings_contribution` after the
action they represent has been persisted, then use the returned events
to notify the user (bot chat message, or Mini App refresh).
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.bootstrap import load_app_context
from app.models.gamification import (
    STREAK_DAILY_LOG,
    Badge,
    UserBadge,
    UserStreak,
    UserXP,
)
from app.models.savings_goal import SavingsGoal
from app.models.transaction import Transaction, TransactionSource

log = logging.getLogger(__name__)


# ---------- Events ----------


@dataclass(frozen=True)
class BadgeEarned:
    badge: Badge


@dataclass(frozen=True)
class LevelUp:
    from_level: int
    to_level: int
    total_xp: int


GamificationEvent = BadgeEarned | LevelUp


# ---------- XP + level ----------


def level_for_xp(total_xp: int, base: int) -> int:
    """Level 1 for < base, level 2 for [base, 2*base), etc. Matches spec's
    "level N requires base * (N-1) cumulative XP" reading.
    """
    if total_xp < 0:
        return 1
    return 1 + (total_xp // max(base, 1))


async def _get_or_create_xp(session: AsyncSession, user_id: int) -> UserXP:
    row = await session.get(UserXP, user_id)
    if row is not None:
        return row
    row = UserXP(user_id=user_id, total_xp=0, level=1)
    session.add(row)
    await session.flush()
    return row


async def award_xp(
    session: AsyncSession, *, user_id: int, amount: int
) -> tuple[UserXP, LevelUp | None]:
    """Add XP, update level, return (row, level_up_event or None)."""
    if amount <= 0:
        row = await _get_or_create_xp(session, user_id)
        return row, None

    base = load_app_context().app.gamification.level_xp_base
    row = await _get_or_create_xp(session, user_id)
    old_level = row.level
    row.total_xp += amount
    new_level = level_for_xp(row.total_xp, base)
    row.level = new_level
    row.updated_at = datetime.now(UTC)
    session.add(row)
    await session.flush()

    level_up = (
        LevelUp(from_level=old_level, to_level=new_level, total_xp=row.total_xp)
        if new_level > old_level
        else None
    )
    return row, level_up


# ---------- Badges ----------


async def _load_badge(session: AsyncSession, badge_id: str) -> Badge | None:
    return await session.get(Badge, badge_id)


async def _has_badge(session: AsyncSession, user_id: int, badge_id: str) -> bool:
    stmt = select(UserBadge.id).where(
        UserBadge.user_id == user_id, UserBadge.badge_id == badge_id
    )
    return (await session.execute(stmt)).scalar_one_or_none() is not None


async def award_badge(
    session: AsyncSession, *, user_id: int, badge_id: str
) -> tuple[BadgeEarned, LevelUp | None] | None:
    """Award a badge if the user doesn't already have it. Adds the badge's
    xp_reward to their XP and returns any resulting level up.
    """
    if await _has_badge(session, user_id, badge_id):
        return None
    badge = await _load_badge(session, badge_id)
    if badge is None:
        log.warning("unknown badge id: %s", badge_id)
        return None

    session.add(UserBadge(user_id=user_id, badge_id=badge_id))
    _, level_up = await award_xp(session, user_id=user_id, amount=badge.xp_reward)
    await session.flush()
    return BadgeEarned(badge=badge), level_up


# ---------- Streaks ----------


def _local_today(tz_name: str, ref: datetime | None = None) -> date:
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        tz = ZoneInfo("UTC")
    return (ref or datetime.now(UTC)).astimezone(tz).date()


async def _get_or_create_streak(
    session: AsyncSession, user_id: int, streak_type: str
) -> UserStreak:
    stmt = select(UserStreak).where(
        UserStreak.user_id == user_id, UserStreak.streak_type == streak_type
    )
    existing = (await session.execute(stmt)).scalars().first()
    if existing is not None:
        return existing
    row = UserStreak(user_id=user_id, streak_type=streak_type)
    session.add(row)
    await session.flush()
    return row


async def bump_daily_log_streak(
    session: AsyncSession, *, user_id: int, tz_name: str
) -> tuple[UserStreak, bool]:
    """Advance the daily-log streak for `today` in the user's tz.

    Returns (row, advanced). `advanced=False` means the user already logged
    something today and the streak count didn't move.
    """
    today = _local_today(tz_name)
    streak = await _get_or_create_streak(session, user_id, STREAK_DAILY_LOG)

    if streak.last_activity_date == today:
        return streak, False

    if streak.last_activity_date == today - timedelta(days=1):
        streak.current_count += 1
    else:
        streak.current_count = 1

    streak.best_count = max(streak.best_count, streak.current_count)
    streak.last_activity_date = today
    session.add(streak)
    await session.flush()
    return streak, True


# ---------- Aggregate stats ----------


async def _count_transactions(session: AsyncSession, user_id: int) -> int:
    stmt = (
        select(func.count())
        .select_from(Transaction)
        .where(Transaction.user_id == user_id, Transaction.is_deleted.is_(False))
    )
    return int((await session.execute(stmt)).scalar_one())


async def _count_ai_transactions(session: AsyncSession, user_id: int) -> int:
    stmt = (
        select(func.count())
        .select_from(Transaction)
        .where(
            Transaction.user_id == user_id,
            Transaction.is_deleted.is_(False),
            Transaction.source == TransactionSource.AI_PARSED,
        )
    )
    return int((await session.execute(stmt)).scalar_one())


async def _any_goal_progress(session: AsyncSession, user_id: int) -> bool:
    from decimal import Decimal

    stmt = select(SavingsGoal.id).where(
        SavingsGoal.user_id == user_id, SavingsGoal.current_amount > Decimal(0)
    )
    return (await session.execute(stmt)).first() is not None


async def list_streaks(session: AsyncSession, user_id: int) -> list[UserStreak]:
    stmt = select(UserStreak).where(UserStreak.user_id == user_id)
    return list((await session.execute(stmt)).scalars().all())


async def list_earned_badges(
    session: AsyncSession, user_id: int
) -> list[tuple[Badge, UserBadge]]:
    stmt = (
        select(UserBadge, Badge)
        .join(Badge, Badge.id == UserBadge.badge_id)
        .where(UserBadge.user_id == user_id)
        .order_by(UserBadge.earned_at)
    )
    return [(badge, ub) for ub, badge in (await session.execute(stmt)).all()]


async def list_all_badges(session: AsyncSession) -> list[Badge]:
    return list((await session.execute(select(Badge).order_by(Badge.id))).scalars().all())


# ---------- Event dispatchers ----------


async def on_transaction_created(
    session: AsyncSession,
    *,
    user_id: int,
    source: TransactionSource,
    tz_name: str,
) -> list[GamificationEvent]:
    """Called right after a transaction has been persisted (either path)."""
    cfg = load_app_context().app.gamification
    events: list[GamificationEvent] = []

    # 1. Base per-transaction XP.
    _, lvl = await award_xp(session, user_id=user_id, amount=cfg.xp_per_transaction)
    if lvl is not None:
        events.append(lvl)

    # 2. Streak advance + streak-day XP.
    streak, advanced = await bump_daily_log_streak(
        session, user_id=user_id, tz_name=tz_name
    )
    if advanced:
        _, lvl = await award_xp(
            session, user_id=user_id, amount=cfg.xp_per_streak_day
        )
        if lvl is not None:
            events.append(lvl)

    # 3. Badges — check the conditions after the transaction is in the DB.
    tx_count = await _count_transactions(session, user_id)
    if tx_count == 1:
        got = await award_badge(session, user_id=user_id, badge_id="first_transaction")
        if got:
            events.append(got[0])
            if got[1] is not None:
                events.append(got[1])

    if source == TransactionSource.AI_PARSED:
        ai_count = await _count_ai_transactions(session, user_id)
        if ai_count == 1:
            got = await award_badge(session, user_id=user_id, badge_id="ai_user")
            if got:
                events.append(got[0])
                if got[1] is not None:
                    events.append(got[1])

    if streak.current_count >= 7:
        got = await award_badge(session, user_id=user_id, badge_id="week_streak")
        if got:
            events.append(got[0])
            if got[1] is not None:
                events.append(got[1])
    if streak.current_count >= 30:
        got = await award_badge(session, user_id=user_id, badge_id="month_streak")
        if got:
            events.append(got[0])
            if got[1] is not None:
                events.append(got[1])
    if tx_count >= 100:
        got = await award_badge(session, user_id=user_id, badge_id="power_user")
        if got:
            events.append(got[0])
            if got[1] is not None:
                events.append(got[1])

    return events


async def on_savings_contribution(
    session: AsyncSession,
    *,
    user_id: int,
    just_completed: bool,
) -> list[GamificationEvent]:
    cfg = load_app_context().app.gamification
    events: list[GamificationEvent] = []

    # saver: earned on any contribution (checks internal idempotency).
    if await _any_goal_progress(session, user_id):
        got = await award_badge(session, user_id=user_id, badge_id="saver")
        if got:
            events.append(got[0])
            if got[1] is not None:
                events.append(got[1])

    if just_completed:
        _, lvl = await award_xp(
            session, user_id=user_id, amount=cfg.xp_per_goal_reached
        )
        if lvl is not None:
            events.append(lvl)
        got = await award_badge(session, user_id=user_id, badge_id="goal_reached")
        if got:
            events.append(got[0])
            if got[1] is not None:
                events.append(got[1])

    return events
