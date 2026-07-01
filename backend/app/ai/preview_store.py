"""Pending transaction previews stored in Redis until the user confirms."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from decimal import Decimal

from redis.asyncio import Redis

DEFAULT_TTL_SECONDS = 15 * 60


@dataclass
class TransactionPreview:
    id: str
    user_id: int
    type: str                   # "income" | "expense" | "transfer"
    amount: str                 # decimal-as-string to keep precision through JSON
    currency: str
    account_id: str
    to_account_id: str | None = None
    category_id: str | None = None
    merchant: str | None = None
    description: str | None = None
    occurred_at_iso: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    raw_input_text: str | None = None
    # A short human-readable summary the bot can show above the confirm
    # buttons — the tool builds this so the agent doesn't have to reformat.
    summary_en: str = ""
    summary_fa: str = ""


def _key(user_id: int, preview_id: str) -> str:
    return f"preview:{user_id}:{preview_id}"


async def save_preview(
    redis: Redis,
    preview: TransactionPreview,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> None:
    payload = json.dumps(asdict(preview))
    await redis.set(_key(preview.user_id, preview.id), payload, ex=ttl_seconds)


async def load_preview(
    redis: Redis, user_id: int, preview_id: str
) -> TransactionPreview | None:
    raw = await redis.get(_key(user_id, preview_id))
    if not raw:
        return None
    data = json.loads(raw)
    return TransactionPreview(**data)


async def discard_preview(redis: Redis, user_id: int, preview_id: str) -> None:
    await redis.delete(_key(user_id, preview_id))


def new_preview_id() -> str:
    return uuid.uuid4().hex[:12]
