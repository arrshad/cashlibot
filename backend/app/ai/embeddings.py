"""Embedding provider — always OpenAI text-embedding-3-small for now.

If OPENAI_API_KEY isn't set, `embed_query` returns None and memory-related
features degrade gracefully instead of raising.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from app.core.config import get_settings
from app.models.memory import EMBEDDING_DIM

log = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-3-small"


@lru_cache(maxsize=1)
def _embeddings():
    """Lazy singleton so we don't build the client until first use."""
    settings = get_settings()
    if not settings.openai_api_key:
        return None
    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=settings.openai_api_key,
        dimensions=EMBEDDING_DIM,
    )


def embeddings_available() -> bool:
    return _embeddings() is not None


async def embed_query(text: str) -> list[float] | None:
    """Return a 1536-d vector, or None if embeddings aren't configured."""
    emb = _embeddings()
    if emb is None:
        return None
    try:
        return await emb.aembed_query(text)
    except Exception:
        log.exception("embedding failed for text length %d", len(text))
        return None
