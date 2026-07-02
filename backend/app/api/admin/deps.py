"""Admin auth dependency."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.admin_auth import InvalidAdminToken, verify_admin_token
from app.core.config import get_settings
from app.core.db import async_session_factory
from app.models.user import User


async def get_admin_session() -> AsyncIterator[AsyncSession]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def _extract_bearer(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "missing Authorization header"
        )
    scheme, _, value = authorization.partition(" ")
    if scheme.lower() != "bearer" or not value:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "expected 'Authorization: Bearer <token>'",
        )
    return value


async def get_current_admin(
    authorization: Annotated[str | None, Header()] = None,
    session: Annotated[AsyncSession, Depends(get_admin_session)] = None,  # type: ignore[assignment]
) -> User:
    token = _extract_bearer(authorization)
    settings = get_settings()
    try:
        claims = verify_admin_token(token, settings.admin_jwt_secret)
    except InvalidAdminToken as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, f"invalid token: {exc}"
        ) from exc

    user = await session.get(User, claims.telegram_id)
    if user is None or not user.is_admin:
        # If we minted a token for a user who was later demoted, this is where
        # we catch it. Better a fresh 401 than serving admin data.
        raise HTTPException(status.HTTP_403_FORBIDDEN, "not an admin")
    return user
