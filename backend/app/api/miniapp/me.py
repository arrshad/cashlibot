"""GET /api/me — current user as seen by the Mini App."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.models.user import User

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


@router.get("/me", response_model=UserOut)
async def get_me(user: Annotated[User, Depends(get_current_user)]) -> UserOut:
    return UserOut(
        telegram_id=user.telegram_id,
        username=user.username,
        display_name=user.display_name,
        language_code=user.language_code,
        calendar_system=user.calendar_system,
        timezone=user.timezone,
        default_currency=user.default_currency,
        credit_balance=user.credit_balance,
        is_admin=user.is_admin,
        onboarding_completed=user.onboarding_completed,
    )
