"""LangChain tools exposed to the agent."""

from __future__ import annotations

import json
import logging
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
from app.models.category import Category
from app.models.memory import MemoryType
from app.services.categorization_service import find_matching_category
from app.services.memory_service import retrieve_relevant, store_memory
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

    tools: list[BaseTool] = [
        get_accounts,
        get_recent_transactions,
        preview_transaction,
        preview_transfer,
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
