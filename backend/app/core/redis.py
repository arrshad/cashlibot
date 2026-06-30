"""Async Redis client, shared across the app."""

from __future__ import annotations

from redis.asyncio import Redis

from app.core.config import get_settings


def make_redis() -> Redis:
    settings = get_settings()
    return Redis.from_url(settings.redis_url, decode_responses=True)
