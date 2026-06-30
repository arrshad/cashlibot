"""User-level operations: lookup, create, update profile fields."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_user(session: AsyncSession, telegram_id: int) -> User | None:
    return await session.get(User, telegram_id)


async def get_or_create_user(
    session: AsyncSession,
    *,
    telegram_id: int,
    username: str | None,
    display_name: str,
    language_hint: str | None,
) -> tuple[User, bool]:
    """Return (user, created). `created=True` if this is the first time we see them."""
    existing = await session.get(User, telegram_id)
    if existing is not None:
        return existing, False

    user = User(
        telegram_id=telegram_id,
        username=username,
        display_name=display_name,
        language_code=_pick_initial_language(language_hint),
    )
    session.add(user)
    await session.flush()
    return user, True


def _pick_initial_language(tg_lang: str | None) -> str:
    if tg_lang and tg_lang.lower().startswith("fa"):
        return "fa"
    return "en"


async def update_user(session: AsyncSession, user: User, **fields: object) -> User:
    """Patch known fields on a user. Always bumps `updated_at`."""
    for key, value in fields.items():
        if not hasattr(user, key):
            raise AttributeError(f"User has no field '{key}'")
        setattr(user, key, value)
    user.updated_at = datetime.now(UTC)
    session.add(user)
    await session.flush()
    return user
