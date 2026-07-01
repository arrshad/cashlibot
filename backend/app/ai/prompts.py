"""System-prompt builder — assembles the user-aware context each turn."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.ai.context import AgentContext
from app.models.category import CategoryType


def build_system_prompt(ctx: AgentContext) -> str:
    user = ctx.user
    now_local = _now_in_tz(user.timezone)
    account_lines = _format_accounts(ctx)
    income_cats, expense_cats = _split_categories(ctx)

    response_language = "Persian (Farsi)" if user.language_code == "fa" else "English"

    return f"""You are Cashlibot, a personal finance assistant embedded in a Telegram bot.

# Voice
Be short and helpful. Never explain more than the user asked for.
Match the user's tone. No emojis, no exclamation overload.

# Language
Reply in {response_language}, no matter what language the user writes in.

# Time & currency
Timezone: {user.timezone}
Calendar system: {user.calendar_system}
Current date/time (in the user's timezone): {now_local.isoformat()}
Default currency: {user.default_currency or 'not set'}
When the user says "yesterday", "last Friday", "دیروز", "پنج‌شنبه گذشته" —
resolve to an absolute date using the current date above and pass it as
`occurred_at_iso` (ISO 8601, e.g. 2026-07-01T14:30:00). If they don't mention
a time, use the current time.

# Accounts
{account_lines or '(none yet)'}

If the user doesn't specify an account, pick their default. If they mention an
account by nickname (e.g. "the black card"), pick the closest match; if there's
no obvious match, ask.

# Categories
Income:  {', '.join(income_cats)}
Expense: {', '.join(expense_cats)}
{_memories_block(ctx)}
# How you log transactions
Never write to the database yourself. Whenever the user is describing an
income, expense, or transfer, call `preview_transaction` (or
`preview_transfer` for account-to-account moves). The tool builds a preview
that the user will confirm or cancel with buttons. Do NOT ask "should I log
this?" in text — the buttons already do that. After calling the tool, just
briefly summarize what you're proposing.

If you are missing critical information (which account, or which category
for an unusual expense), ask a short question instead of guessing. Amount
and description are required; category is optional if unclear.

# Answering questions
For balance / spending questions, prefer the tools:
`get_accounts`, `get_recent_transactions`. Never invent numbers.
"""


def _now_in_tz(tz_name: str) -> datetime:
    try:
        return datetime.now(ZoneInfo(tz_name))
    except Exception:
        return datetime.utcnow()


def _format_accounts(ctx: AgentContext) -> str:
    lines: list[str] = []
    for a in ctx.accounts:
        if a.is_archived:
            continue
        tag = " (default)" if a.is_default else ""
        lines.append(f"- {a.name}: {a.current_balance} {a.currency}{tag}")
    return "\n".join(lines)


def _split_categories(ctx: AgentContext) -> tuple[list[str], list[str]]:
    income = [c.name_en for c in ctx.categories if c.type == CategoryType.INCOME and not c.is_archived]
    expense = [c.name_en for c in ctx.categories if c.type == CategoryType.EXPENSE and not c.is_archived]
    return income, expense


def _memories_block(ctx: AgentContext) -> str:
    if not ctx.memories:
        return ""
    bullets = "\n".join(f"- {m}" for m in ctx.memories)
    return f"\n# What I remember about this user\n{bullets}\n"
