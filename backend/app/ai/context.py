"""Per-invocation context passed to every agent tool via closure."""

from __future__ import annotations

from dataclasses import dataclass, field

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.category import Category
from app.models.user import User


@dataclass
class AgentContext:
    user: User
    session: AsyncSession
    redis: Redis
    # Prefetched so tool calls don't have to re-hit the DB every time the
    # agent asks about accounts / categories in the same turn.
    accounts: list[Account]
    categories: list[Category]
    # Collected side-effects — every preview id the tools push here is
    # surfaced to the bot handler so it can render confirm/cancel buttons.
    pending_preview_ids: list[str] = field(default_factory=list)
    # Original user message. Stored so tools can attach it to the transaction
    # as raw_input_text when they preview.
    raw_input_text: str = ""
