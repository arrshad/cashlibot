"""Semantic memory: store + retrieve user-scoped facts via pgvector."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import embed_query, embeddings_available
from app.models.memory import MemoryType, UserMemory

log = logging.getLogger(__name__)

# Cosine distance < this means "same memory, update it". distance = 1 - similarity.
_DEDUP_DISTANCE = 0.08
_DEFAULT_TOP_K = 5


async def store_memory(
    session: AsyncSession,
    *,
    user_id: int,
    content: str,
    memory_type: MemoryType,
    metadata: dict | None = None,
) -> UserMemory | None:
    """Persist a memory. No-op (returns None) if embeddings aren't configured.

    Reuses an existing memory of the same type if one is close enough by
    cosine distance — keeps memory count bounded and lets users overwrite
    their own preferences by restating them.
    """
    content = content.strip()
    if not content:
        return None
    if not embeddings_available():
        log.debug("memory skipped: embeddings not configured")
        return None

    vector = await embed_query(content)
    if vector is None:
        return None

    metadata_json = json.dumps(metadata) if metadata else None

    stmt = (
        select(
            UserMemory,
            UserMemory.embedding.cosine_distance(vector).label("dist"),
        )
        .where(
            UserMemory.user_id == user_id,
            UserMemory.memory_type == memory_type,
        )
        .order_by("dist")
        .limit(1)
    )
    row = (await session.execute(stmt)).first()

    if row is not None and row.dist is not None and row.dist < _DEDUP_DISTANCE:
        existing: UserMemory = row.UserMemory
        existing.content = content
        existing.embedding = vector
        existing.metadata_json = metadata_json
        existing.updated_at = datetime.now(UTC)
        session.add(existing)
        await session.flush()
        return existing

    memory = UserMemory(
        user_id=user_id,
        memory_type=memory_type,
        content=content,
        embedding=vector,
        metadata_json=metadata_json,
    )
    session.add(memory)
    await session.flush()
    return memory


async def retrieve_relevant(
    session: AsyncSession,
    *,
    user_id: int,
    query: str,
    top_k: int = _DEFAULT_TOP_K,
) -> list[str]:
    """Semantic top-k lookup. Returns memory contents ordered by relevance."""
    if not embeddings_available():
        return []
    vector = await embed_query(query)
    if vector is None:
        return []

    stmt = (
        select(UserMemory)
        .where(UserMemory.user_id == user_id)
        .order_by(UserMemory.embedding.cosine_distance(vector))
        .limit(top_k)
    )
    result = await session.execute(stmt)
    return [m.content for m in result.scalars().all()]
