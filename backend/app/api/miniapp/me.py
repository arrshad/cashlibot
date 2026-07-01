"""GET /api/me + PATCH /api/me."""

from __future__ import annotations

from typing import Annotated, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.core.bootstrap import load_app_context
from app.models.user import User
from app.services.user_service import update_user

router = APIRouter()


class UserOut(BaseModel):
    telegram_id: int
    username: str | None
    display_name: str
    language_code: str
    calendar_system: str
    timezone: str
    default_currency: str | None
    credit_balance: int
    is_admin: bool
    onboarding_completed: bool

    @classmethod
    def from_model(cls, u: User) -> "UserOut":
        return cls(
            telegram_id=u.telegram_id,
            username=u.username,
            display_name=u.display_name,
            language_code=u.language_code,
            calendar_system=u.calendar_system,
            timezone=u.timezone,
            default_currency=u.default_currency,
            credit_balance=u.credit_balance,
            is_admin=u.is_admin,
            onboarding_completed=u.onboarding_completed,
        )


class UserPatchIn(BaseModel):
    language_code: Literal["en", "fa"] | None = None
    calendar_system: Literal["gregorian", "jalali", "hijri"] | None = None
    timezone: str | None = None
    default_currency: str | None = Field(default=None, min_length=2, max_length=5)


@router.get("/me", response_model=UserOut)
async def get_me(user: Annotated[User, Depends(get_current_user)]) -> UserOut:
    return UserOut.from_model(user)


@router.patch("/me", response_model=UserOut)
async def patch_me(
    payload: UserPatchIn,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserOut:
    fields = payload.model_dump(exclude_unset=True)
    if not fields:
        return UserOut.from_model(user)

    ctx = load_app_context()
    if "default_currency" in fields and not ctx.currencies.is_enabled(
        fields["default_currency"]
    ):
        raise HTTPException(400, f"unknown currency: {fields['default_currency']}")

    if "timezone" in fields:
        try:
            ZoneInfo(fields["timezone"])
        except ZoneInfoNotFoundError as exc:
            raise HTTPException(400, f"unknown timezone: {fields['timezone']}") from exc

    await update_user(session, user, **fields)
    return UserOut.from_model(user)
