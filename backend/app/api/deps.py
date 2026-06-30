"""FastAPI dependencies shared across routers."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import async_session_factory
from app.core.telegram_auth import (
    InvalidInitData,
    ParsedInitData,
    validate_init_data,
)
from app.models.user import User
from app.services.user_service import get_or_create_user


async def get_session() -> AsyncIterator[AsyncSession]:
    """Per-request session. Commits on clean return, rolls back on exception."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def _extract_init_data(authorization: str | None) -> str:
    """`Authorization: tma <init_data>` per the Mini Apps spec."""
    if not authorization:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "missing Authorization header",
        )
    scheme, _, value = authorization.partition(" ")
    if scheme.lower() != "tma" or not value:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "expected 'Authorization: tma <init_data>'",
        )
    return value


def get_init_data(
    authorization: Annotated[str | None, Header()] = None,
) -> ParsedInitData:
    init_data = _extract_init_data(authorization)
    settings = get_settings()
    try:
        return validate_init_data(init_data, settings.telegram_bot_token)
    except InvalidInitData as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, f"invalid init data: {exc}"
        ) from exc


async def get_current_user(
    init: Annotated[ParsedInitData, Depends(get_init_data)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """Load (or create on first call) the User backing this initData."""
    user, _ = await get_or_create_user(
        session,
        telegram_id=init.user.id,
        username=init.user.username,
        display_name=init.user.full_name,
        language_hint=init.user.language_code,
    )
    return user
