"""LangChain tools exposed to the agent."""

from __future__ import annotations

import json
import logging
import uuid as _uuid
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

from langchain_core.tools import BaseTool, tool

from app.ai.context import AgentContext
from app.ai.embeddings import embeddings_available
from app.ai.preview_store import (
    TransactionPreview,
    new_preview_id,
    save_preview,
)
from app.models.account import Account
from app.models.budget import BudgetPeriod
from app.models.category import Category
from app.models.frequency import Frequency
from app.models.memory import MemoryType
from app.models.reminder import ReminderType
from app.services.budget_service import (
    BudgetError,
    create_budget,
    list_with_usage,
)
from app.services.categorization_service import find_matching_category
from app.services.memory_service import retrieve_relevant, store_memory
from app.services.gamification_service import (
    _get_or_create_xp,
    list_earned_badges,
    list_streaks,
    on_savings_contribution,
)
from app.services.reminder_service import (
    ReminderError,
    create_reminder,
    delete_reminder as delete_reminder_service,
    get_reminder as get_reminder_service,
    list_reminders,
)
from app.services.savings_service import (
    SavingsError,
    add_contribution,
    create_goal,
    list_goals,
)
from app.services.transaction_service import list_transactions

log = logging.getLogger(__name__)


def build_tools(ctx: AgentContext) -> list[BaseTool]:
    """Return the tool set bound to this context."""

    @tool
    async def get_accounts() -> str:
        """Return a JSON list of the user's active accounts with balances."""
        payload = [
            {
                "name": a.name,
                "type": a.type.value,
                "currency": a.currency,
                "balance": str(a.current_balance),
                "is_default": a.is_default,
            }
            for a in ctx.accounts
            if not a.is_archived
        ]
        return json.dumps(payload)

    @tool
    async def get_recent_transactions(limit: int = 5) -> str:
        """List the user's most recent (non-deleted) transactions as JSON. limit is capped at 20."""
        capped = max(1, min(int(limit), 20))
        txs = await list_transactions(
            ctx.session, user_id=ctx.user.telegram_id, limit=capped
        )
        payload = [
            {
                "type": t.type.value,
                "amount": str(t.amount),
                "currency": t.currency,
                "merchant": t.merchant,
                "description": t.description,
                "occurred_at": t.occurred_at.isoformat(),
                "account_id": str(t.account_id),
            }
            for t in txs
        ]
        return json.dumps(payload)

    @tool
    async def preview_transaction(
        type: str,
        amount: str,
        account: str,
        category: str | None = None,
        merchant: str | None = None,
        description: str | None = None,
        occurred_at_iso: str | None = None,
    ) -> str:
        """Propose an income or expense transaction and stage it for user confirmation.

        Args:
            type: "income" or "expense".
            amount: decimal amount as a string, e.g. "25.50".
            account: name of the account to log against. Match one of the user's accounts.
            category: optional category name (English, e.g. "Food"). Omit if unclear.
            merchant: optional merchant / payer / payee.
            description: optional short note.
            occurred_at_iso: ISO 8601 datetime. Defaults to now.
        """
        if type not in ("income", "expense"):
            return f"error: type must be 'income' or 'expense', got {type!r}"

        try:
            decimal_amount = Decimal(amount.strip())
        except (InvalidOperation, AttributeError):
            return f"error: amount {amount!r} is not a valid decimal"
        if decimal_amount <= 0:
            return "error: amount must be positive"

        matched = _match_account(ctx.accounts, account)
        if matched is None:
            available = ", ".join(a.name for a in ctx.accounts if not a.is_archived)
            return (
                f"error: no account matches {account!r}. Available: {available}"
            )

        category_id: str | None = None
        if category:
            cat = _match_category(ctx.categories, category, type)
            if cat is None:
                return (
                    f"error: no {type} category matches {category!r}. "
                    "Omit the category argument if unsure."
                )
            category_id = str(cat.id)
        else:
            # No category from the LLM — try to auto-fill from a learned rule
            # (merchant first, then description, then the raw user message).
            hint = merchant or description or ctx.raw_input_text
            if hint:
                rule_hit = await find_matching_category(
                    ctx.session, user_id=ctx.user.telegram_id, text=hint
                )
                if rule_hit is not None:
                    category_id = str(rule_hit)

        occurred_at = _parse_iso(occurred_at_iso) or datetime.now(UTC)

        preview = TransactionPreview(
            id=new_preview_id(),
            user_id=ctx.user.telegram_id,
            type=type,
            amount=str(decimal_amount),
            currency=matched.currency,
            account_id=str(matched.id),
            category_id=category_id,
            merchant=merchant,
            description=description,
            occurred_at_iso=occurred_at.isoformat(),
            raw_input_text=ctx.raw_input_text or None,
            summary_en=_summary(
                lang="en",
                type=type,
                amount=decimal_amount,
                currency=matched.currency,
                account=matched.name,
                merchant=merchant,
                description=description,
                occurred_at=occurred_at,
            ),
            summary_fa=_summary(
                lang="fa",
                type=type,
                amount=decimal_amount,
                currency=matched.currency,
                account=matched.name,
                merchant=merchant,
                description=description,
                occurred_at=occurred_at,
            ),
        )
        await save_preview(ctx.redis, preview)
        ctx.pending_preview_ids.append(preview.id)
        log.info(
            "preview created: user=%s type=%s amount=%s",
            ctx.user.telegram_id, type, decimal_amount,
        )
        return (
            "Preview staged. The user will confirm or cancel via buttons. "
            f"Summary: {preview.summary_en}"
        )

    @tool
    async def preview_transfer(
        amount: str,
        from_account: str,
        to_account: str,
        description: str | None = None,
        occurred_at_iso: str | None = None,
    ) -> str:
        """Propose a transfer between two of the user's accounts (same currency only for now)."""
        try:
            decimal_amount = Decimal(amount.strip())
        except (InvalidOperation, AttributeError):
            return f"error: amount {amount!r} is not a valid decimal"
        if decimal_amount <= 0:
            return "error: amount must be positive"

        src = _match_account(ctx.accounts, from_account)
        dst = _match_account(ctx.accounts, to_account)
        if src is None or dst is None:
            available = ", ".join(a.name for a in ctx.accounts if not a.is_archived)
            return f"error: unknown account. Available: {available}"
        if src.id == dst.id:
            return "error: source and destination must differ"
        if src.currency != dst.currency:
            return (
                f"error: transfer between different currencies "
                f"({src.currency} vs {dst.currency}) is not supported yet"
            )

        occurred_at = _parse_iso(occurred_at_iso) or datetime.now(UTC)

        preview = TransactionPreview(
            id=new_preview_id(),
            user_id=ctx.user.telegram_id,
            type="transfer",
            amount=str(decimal_amount),
            currency=src.currency,
            account_id=str(src.id),
            to_account_id=str(dst.id),
            description=description,
            occurred_at_iso=occurred_at.isoformat(),
            raw_input_text=ctx.raw_input_text or None,
            summary_en=(
                f"Transfer {decimal_amount} {src.currency} "
                f"from {src.name} to {dst.name}"
            ),
            summary_fa=(
                f"انتقال {decimal_amount} {src.currency} "
                f"از {src.name} به {dst.name}"
            ),
        )
        await save_preview(ctx.redis, preview)
        ctx.pending_preview_ids.append(preview.id)
        return (
            "Transfer preview staged. The user will confirm or cancel via buttons. "
            f"Summary: {preview.summary_en}"
        )

    @tool
    async def get_budgets() -> str:
        """List the user's active budgets with current-period usage (spent, ratio, period end)."""
        usages = await list_with_usage(
            ctx.session, user_id=ctx.user.telegram_id, tz_name=ctx.user.timezone
        )
        payload = [
            {
                "category_id": str(u.budget.category_id),
                "category": _category_name(ctx.categories, u.budget.category_id),
                "amount": str(u.budget.amount),
                "spent": str(u.spent),
                "currency": u.budget.currency,
                "period": u.budget.period.value,
                "ratio": float(u.ratio),
                "period_end": u.period_end.isoformat(),
            }
            for u in usages
        ]
        return json.dumps(payload)

    @tool
    async def create_budget_tool(
        category: str,
        amount: str,
        period: str,
        currency: str | None = None,
    ) -> str:
        """Set (or update) a spending budget for one category.

        Args:
            category: category name (e.g. "Food"). Must be one of the user's expense categories.
            amount: decimal limit as a string, e.g. "500".
            period: "weekly", "monthly", or "yearly".
            currency: optional currency code; defaults to the user's default currency.
        """
        cat = _match_category(ctx.categories, category, "expense")
        if cat is None:
            return f"error: no expense category matches {category!r}"
        try:
            decimal_amount = Decimal(amount.strip())
        except (InvalidOperation, AttributeError):
            return f"error: amount {amount!r} is not a valid decimal"
        try:
            period_enum = BudgetPeriod(period.strip().lower())
        except ValueError:
            return "error: period must be 'weekly', 'monthly', or 'yearly'"

        currency_code = (currency or ctx.user.default_currency or "").upper()
        if not currency_code:
            return "error: no currency specified and user has no default"

        try:
            budget = await create_budget(
                ctx.session,
                user_id=ctx.user.telegram_id,
                category_id=cat.id,
                amount=decimal_amount,
                currency=currency_code,
                period=period_enum,
            )
        except BudgetError as exc:
            return f"error: {exc}"
        return (
            f"Budget set: {budget.amount} {budget.currency} "
            f"for {cat.name_en} per {budget.period.value}."
        )

    # LangChain registers each @tool under its function's name. Rename so the
    # LLM sees "create_budget" rather than "create_budget_tool".
    create_budget_tool.name = "create_budget"

    @tool
    async def get_savings_goals() -> str:
        """List the user's savings goals with target, current, and completion."""
        goals = await list_goals(ctx.session, ctx.user.telegram_id)
        payload = [
            {
                "id": str(g.id),
                "name": g.name,
                "target": str(g.target_amount),
                "current": str(g.current_amount),
                "currency": g.currency,
                "deadline": g.deadline.isoformat() if g.deadline else None,
                "is_completed": g.is_completed,
                "ratio": float(
                    g.current_amount / g.target_amount if g.target_amount > 0 else 0
                ),
            }
            for g in goals
        ]
        return json.dumps(payload)

    @tool
    async def create_savings_goal(
        name: str,
        target_amount: str,
        currency: str | None = None,
        deadline: str | None = None,
    ) -> str:
        """Create a new savings goal.

        Args:
            name: short label (e.g. "New laptop").
            target_amount: decimal target as string, e.g. "1500".
            currency: currency code; defaults to the user's default.
            deadline: optional ISO date (YYYY-MM-DD) the user wants to reach the target by.
        """
        try:
            amount = Decimal(target_amount.strip())
        except (InvalidOperation, AttributeError):
            return f"error: target_amount {target_amount!r} is not a valid decimal"

        currency_code = (currency or ctx.user.default_currency or "").upper()
        if not currency_code:
            return "error: no currency provided and user has no default"

        deadline_date = None
        if deadline:
            try:
                deadline_date = datetime.fromisoformat(deadline).date()
            except ValueError:
                return "error: deadline must be YYYY-MM-DD"

        try:
            goal = await create_goal(
                ctx.session,
                user_id=ctx.user.telegram_id,
                name=name,
                target_amount=amount,
                currency=currency_code,
                deadline=deadline_date,
            )
        except SavingsError as exc:
            return f"error: {exc}"
        return f"Goal created: {goal.name} ({goal.target_amount} {goal.currency})."

    @tool
    async def add_to_savings_goal(goal_name: str, amount: str) -> str:
        """Log a contribution to a savings goal.

        Args:
            goal_name: name of the goal (case-insensitive match).
            amount: decimal amount as string.
        """
        try:
            decimal_amount = Decimal(amount.strip())
        except (InvalidOperation, AttributeError):
            return f"error: amount {amount!r} is not a valid decimal"

        goals = await list_goals(ctx.session, ctx.user.telegram_id)
        q = goal_name.strip().casefold()
        match = next(
            (g for g in goals if g.name.casefold() == q),
            None,
        ) or next(
            (g for g in goals if q in g.name.casefold()),
            None,
        )
        if match is None:
            available = ", ".join(g.name for g in goals) or "(none)"
            return f"error: no savings goal matches {goal_name!r}. Available: {available}"

        try:
            updated, just_completed = await add_contribution(
                ctx.session, goal=match, amount=decimal_amount
            )
        except SavingsError as exc:
            return f"error: {exc}"

        # Gamification for AI-driven contributions runs here (no preview flow).
        await on_savings_contribution(
            ctx.session, user_id=ctx.user.telegram_id, just_completed=just_completed
        )

        suffix = " Goal reached." if just_completed else ""
        return (
            f"Added {decimal_amount} {updated.currency} to {updated.name}. "
            f"Now {updated.current_amount} / {updated.target_amount}.{suffix}"
        )

    @tool
    async def get_user_stats() -> str:
        """Return the user's level, XP, streaks, and earned badges as JSON."""
        xp = await _get_or_create_xp(ctx.session, ctx.user.telegram_id)
        streaks = await list_streaks(ctx.session, ctx.user.telegram_id)
        earned = await list_earned_badges(ctx.session, ctx.user.telegram_id)
        payload = {
            "level": xp.level,
            "total_xp": xp.total_xp,
            "streaks": [
                {
                    "type": s.streak_type,
                    "current": s.current_count,
                    "best": s.best_count,
                }
                for s in streaks
            ],
            "badges_earned": [
                {"id": b.id, "name": b.name, "earned_at": ub.earned_at.isoformat()}
                for b, ub in earned
            ],
        }
        return json.dumps(payload)

    @tool
    async def create_reminder_tool(
        title: str,
        due_at_iso: str,
        description: str | None = None,
        reminder_type: str = "custom",
        repeat_frequency: str | None = None,
    ) -> str:
        """Create a chat reminder.

        Args:
            title: short label the user will see when it fires.
            due_at_iso: ISO 8601 datetime when the reminder should fire. Include
                timezone if you know it; UTC is assumed otherwise.
            description: optional longer body.
            reminder_type: one of transaction_log | pay_someone | bill_due |
                monthly_review | custom. Defaults to custom.
            repeat_frequency: daily | weekly | monthly | yearly for repeating
                reminders. Omit for one-shot.
        """
        try:
            due_at = datetime.fromisoformat(due_at_iso.replace("Z", "+00:00"))
        except ValueError:
            return f"error: due_at_iso {due_at_iso!r} isn't a valid ISO datetime"
        if due_at.tzinfo is None:
            due_at = due_at.replace(tzinfo=UTC)

        try:
            r_type = ReminderType(reminder_type)
        except ValueError:
            allowed = ", ".join(t.value for t in ReminderType)
            return f"error: reminder_type must be one of {allowed}"

        freq: Frequency | None = None
        if repeat_frequency:
            try:
                freq = Frequency(repeat_frequency)
            except ValueError:
                return "error: repeat_frequency must be daily / weekly / monthly / yearly"

        try:
            reminder = await create_reminder(
                ctx.session,
                user_id=ctx.user.telegram_id,
                title=title,
                due_at=due_at,
                reminder_type=r_type,
                description=description,
                repeat_frequency=freq,
            )
        except ReminderError as exc:
            return f"error: {exc}"
        return (
            f"Reminder set: {reminder.title} at {reminder.due_at.isoformat()}"
            + (f" (repeats {freq.value})" if freq else "")
        )

    # Give the LLM the cleaner name.
    create_reminder_tool.name = "create_reminder"

    @tool
    async def get_reminders() -> str:
        """List the user's active reminders as JSON."""
        rows = await list_reminders(ctx.session, ctx.user.telegram_id)
        return json.dumps(
            [
                {
                    "id": str(r.id),
                    "title": r.title,
                    "due_at": r.due_at.isoformat(),
                    "repeat_frequency": r.repeat_frequency.value
                    if r.repeat_frequency
                    else None,
                    "type": r.reminder_type.value,
                }
                for r in rows
            ]
        )

    @tool
    async def delete_reminder_tool(reminder_id: str) -> str:
        """Delete a reminder by its id (get it from get_reminders)."""
        try:
            uid = _uuid.UUID(reminder_id)
        except (ValueError, TypeError):
            return f"error: invalid reminder id {reminder_id!r}"
        reminder = await get_reminder_service(
            ctx.session, reminder_id=uid, user_id=ctx.user.telegram_id
        )
        if reminder is None:
            return "error: reminder not found"
        await delete_reminder_service(ctx.session, reminder)
        return f"Deleted reminder: {reminder.title}."

    delete_reminder_tool.name = "delete_reminder"

    tools: list[BaseTool] = [
        get_accounts,
        get_recent_transactions,
        preview_transaction,
        preview_transfer,
        get_budgets,
        create_budget_tool,
        get_savings_goals,
        create_savings_goal,
        add_to_savings_goal,
        get_user_stats,
        create_reminder_tool,
        get_reminders,
        delete_reminder_tool,
    ]

    # Memory tools only make sense when embeddings are configured. Registering
    # them conditionally keeps the LLM from calling into a dead code path.
    if embeddings_available():

        @tool
        async def remember(content: str, memory_type: str = "preference") -> str:
            """Persist a fact or preference about the user for future turns.

            memory_type: one of preference | account_default | category_habit | contact | context.
            Use this when the user states a lasting rule ("I always pay Netflix from the black card",
            "my rent is 800 EUR"). Don't use it for one-off events — those go through transactions.
            """
            try:
                mem_type = MemoryType(memory_type)
            except ValueError:
                allowed = ", ".join(m.value for m in MemoryType)
                return f"error: memory_type must be one of {allowed}"
            stored = await store_memory(
                ctx.session,
                user_id=ctx.user.telegram_id,
                content=content,
                memory_type=mem_type,
            )
            if stored is None:
                return "error: memory subsystem not available"
            return f"Stored ({mem_type.value})."

        @tool
        async def search_memories(query: str, top_k: int = 5) -> str:
            """Semantic search of the user's stored preferences and habits."""
            capped = max(1, min(int(top_k), 10))
            hits = await retrieve_relevant(
                ctx.session,
                user_id=ctx.user.telegram_id,
                query=query,
                top_k=capped,
            )
            if not hits:
                return "no relevant memories"
            return json.dumps(hits)

        tools.extend([remember, search_memories])

    return tools


# ---------- internal helpers ----------


def _match_account(accounts: list[Account], query: str) -> Account | None:
    q = query.strip().casefold()
    active = [a for a in accounts if not a.is_archived]
    for a in active:
        if a.name.casefold() == q:
            return a
    for a in active:
        if q in a.name.casefold():
            return a
    return None


def _category_name(categories: list[Category], category_id) -> str:
    """Best-effort lookup of a category's user-facing name from its id."""
    key = _uuid.UUID(str(category_id))
    for c in categories:
        if c.id == key:
            return c.name_en or c.name
    return "?"


def _match_category(
    categories: list[Category], query: str, tx_type: str
) -> Category | None:
    from app.models.category import CategoryType

    target = CategoryType.INCOME if tx_type == "income" else CategoryType.EXPENSE
    q = query.strip().casefold()
    candidates = [
        c for c in categories if c.type == target and not c.is_archived
    ]
    for c in candidates:
        if c.name_en.casefold() == q or c.name.casefold() == q:
            return c
        if c.name_fa and c.name_fa.casefold() == q:
            return c
    for c in candidates:
        if q in c.name_en.casefold() or q in c.name.casefold():
            return c
    return None


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def _summary(
    *,
    lang: str,
    type: str,
    amount: Decimal,
    currency: str,
    account: str,
    merchant: str | None,
    description: str | None,
    occurred_at: datetime,
) -> str:
    """Short natural-language preview shown above the confirm buttons."""
    who_or_note = merchant or description or ""
    when = occurred_at.date().isoformat()
    if lang == "fa":
        head = {"income": "درآمد", "expense": "هزینه"}.get(type, type)
        parts = [f"{head}: {amount} {currency}", f"حساب: {account}"]
        if who_or_note:
            parts.append(f"بابت: {who_or_note}")
        parts.append(f"تاریخ: {when}")
        return " · ".join(parts)
    head = type.capitalize()
    parts = [f"{head}: {amount} {currency}", f"account: {account}"]
    if who_or_note:
        parts.append(f"for: {who_or_note}")
    parts.append(f"on {when}")
    return " · ".join(parts)
