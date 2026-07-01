"""Categorization rules: learned merchant/keyword → category mappings."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.categorization_rule import CategorizationRule


def _normalize(text: str) -> str:
    return text.strip().casefold()


async def upsert_rule(
    session: AsyncSession,
    *,
    user_id: int,
    keyword: str,
    category_id: uuid.UUID,
) -> CategorizationRule:
    """Create or bump a rule for this user + keyword."""
    key = _normalize(keyword)
    if not key:
        raise ValueError("empty keyword")

    stmt = select(CategorizationRule).where(
        CategorizationRule.user_id == user_id,
        CategorizationRule.merchant_or_keyword == key,
    )
    existing = (await session.execute(stmt)).scalars().first()

    now = datetime.now(UTC)
    if existing is not None:
        existing.category_id = category_id
        existing.match_count += 1
        existing.last_used_at = now
        session.add(existing)
        await session.flush()
        return existing

    rule = CategorizationRule(
        user_id=user_id,
        merchant_or_keyword=key,
        category_id=category_id,
        match_count=1,
        last_used_at=now,
    )
    session.add(rule)
    await session.flush()
    return rule


async def find_matching_category(
    session: AsyncSession, *, user_id: int, text: str
) -> uuid.UUID | None:
    """Find a category for this free-form text using the user's stored rules.

    Matches are substring on the normalized keyword. The rule with the highest
    match_count wins when several apply; ties break on most-recently-used.
    """
    if not text:
        return None
    body = _normalize(text)

    stmt = select(CategorizationRule).where(CategorizationRule.user_id == user_id)
    rules = list((await session.execute(stmt)).scalars().all())
    matches = [r for r in rules if r.merchant_or_keyword in body]
    if not matches:
        return None
    matches.sort(
        key=lambda r: (r.match_count, r.last_used_at or datetime.min.replace(tzinfo=UTC)),
        reverse=True,
    )
    return matches[0].category_id


async def bump_match(session: AsyncSession, rule: CategorizationRule) -> None:
    rule.match_count += 1
    rule.last_used_at = datetime.now(UTC)
    session.add(rule)
    await session.flush()
