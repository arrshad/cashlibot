"""Weekly digest: compose a recap of a user's last 7 days.

Returns None when the week had zero activity — we don't spam users who
didn't use the bot, and it lets the scheduler skip them without special-casing.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.bootstrap import load_app_context
from app.i18n import get_i18n
from app.models.gamification import STREAK_DAILY_LOG, UserStreak
from app.models.user import User
from app.services import analytics_service
from app.services.budget_service import EXCEED_RATIO, WARN_RATIO, list_with_usage

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class DigestPayload:
    text: str
    tx_count: int  # returned for logging / tests; ignored when sending


def _tz(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def _format_amount(amount: Decimal, currency: str) -> str:
    """Currency-aware formatting using the YAML currency catalog."""
    ctx = load_app_context()
    conf = ctx.currencies.get(currency)
    if conf is None:
        # Fall back to a bare number if the currency isn't in the catalog.
        return f"{amount} {currency}"
    quantized = round(amount, conf.decimal_places)
    formatted = f"{quantized:,.{conf.decimal_places}f}"
    formatted = formatted.replace(",", "§").replace(
        ".", conf.decimal_separator
    ).replace("§", conf.thousands_separator)
    if conf.symbol_position == "before":
        return f"{conf.symbol}{formatted}"
    return f"{formatted} {conf.symbol}"


async def _weekly_totals(
    session: AsyncSession, *, user: User, start: datetime, end: datetime
) -> tuple[dict[str, Decimal], int]:
    """Per-currency expense totals plus a total tx count for the window."""
    totals = await analytics_service.get_income_vs_expense(
        session, user_id=user.telegram_id, start=start, end=end
    )
    expense_totals = {cur: t.expense for cur, t in totals.items() if t.expense > 0}
    tx_count = 0
    for t in totals.values():
        if t.income > 0 or t.expense > 0:
            # Rough count proxy for "had activity" — we don't need the exact
            # number for the recap text, but keep it around for the tick log.
            tx_count += 1
    return expense_totals, tx_count


async def _current_streak(session: AsyncSession, user_id: int) -> int:
    from sqlalchemy import select

    stmt = select(UserStreak).where(
        UserStreak.user_id == user_id,
        UserStreak.streak_type == STREAK_DAILY_LOG,
    )
    row = (await session.execute(stmt)).scalars().first()
    return int(row.current_count) if row else 0


async def build_digest(
    session: AsyncSession, *, user: User
) -> DigestPayload | None:
    """Compose the weekly digest text for a user, or None if they had no activity."""
    lang = user.language_code
    tz_name = user.timezone
    tz = _tz(tz_name)

    now_local = datetime.now(UTC).astimezone(tz)
    week_end_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start_local = week_end_local - timedelta(days=7)
    start_utc = week_start_local.astimezone(UTC)
    end_utc = week_end_local.astimezone(UTC)

    expense_totals, tx_count = await _weekly_totals(
        session, user=user, start=start_utc, end=end_utc
    )
    top_categories = await analytics_service.get_spending_by_category(
        session,
        user_id=user.telegram_id,
        start=start_utc,
        end=end_utc,
        limit=3,
    )

    if not expense_totals and not top_categories:
        return None

    i18n = get_i18n()

    def t(key: str, **fmt: object) -> str:
        return i18n.t(lang, key, **fmt)

    lines: list[str] = [t("digest.header")]

    if expense_totals:
        totals_str = ", ".join(
            _format_amount(amount, currency)
            for currency, amount in expense_totals.items()
        )
        lines.append("")
        lines.append(t("digest.spent", totals=totals_str))

    if top_categories:
        lines.append("")
        lines.append(t("digest.top_categories_header"))
        for row in top_categories:
            lines.append(
                t(
                    "digest.top_category_row",
                    name=row.name,
                    amount=_format_amount(row.amount, row.currency),
                )
            )

    # Budget hotspots (warning / exceeded this period).
    usages = await list_with_usage(
        session, user_id=user.telegram_id, tz_name=tz_name
    )
    hotspots: list[str] = []
    for usage in usages:
        if usage.ratio >= EXCEED_RATIO:
            hotspots.append(
                t(
                    "digest.budget_exceeded",
                    percent=int(usage.ratio * 100),
                    spent=_format_amount(usage.spent, usage.budget.currency),
                    limit=_format_amount(usage.budget.amount, usage.budget.currency),
                )
            )
        elif usage.ratio >= WARN_RATIO:
            hotspots.append(
                t(
                    "digest.budget_warning",
                    percent=int(usage.ratio * 100),
                    spent=_format_amount(usage.spent, usage.budget.currency),
                    limit=_format_amount(usage.budget.amount, usage.budget.currency),
                )
            )
    if hotspots:
        lines.append("")
        lines.append(t("digest.budgets_header"))
        lines.extend(hotspots)

    streak_days = await _current_streak(session, user.telegram_id)
    if streak_days > 0:
        lines.append("")
        lines.append(t("digest.streak", days=streak_days))

    # Behavior score — cheap to compute, adds a "how am I doing" signal.
    score = await analytics_service.compute_behavior_score(
        session, user_id=user.telegram_id, tz_name=tz_name
    )
    lines.append("")
    lines.append(t("digest.behavior_score", score=score.total))

    lines.append("")
    lines.append(t("digest.footer"))

    return DigestPayload(text="\n".join(lines), tx_count=tx_count)
