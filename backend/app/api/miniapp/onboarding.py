"""POST /api/onboarding/complete — atomic onboarding write."""

from __future__ import annotations

from typing import Annotated, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.api.miniapp.config import ACCOUNT_TYPE_ICONS
from app.core.bootstrap import load_app_context
from app.models.account import AccountType
from app.models.credit import CreditReason
from app.models.user import User
from app.services.account_service import create_account
from app.services.category_service import seed_default_categories
from app.services.credit_service import add_credits
from app.services.user_service import update_user

router = APIRouter()


class FirstAccountIn(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    type: AccountType
    currency: str = Field(min_length=2, max_length=5)


class OnboardingIn(BaseModel):
    language_code: Literal["en", "fa"]
    calendar_system: Literal["gregorian", "jalali", "hijri"]
    timezone: str
    default_currency: str = Field(min_length=2, max_length=5)
    first_account: FirstAccountIn


class OnboardingOut(BaseModel):
    onboarding_completed: bool
    credit_balance: int
    signup_credits_granted: int


@router.post(
    "/onboarding/complete",
    response_model=OnboardingOut,
    status_code=status.HTTP_200_OK,
)
async def complete_onboarding(
    payload: OnboardingIn,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> OnboardingOut:
    ctx = load_app_context()

    if not ctx.currencies.is_enabled(payload.default_currency):
        raise HTTPException(400, f"unknown currency: {payload.default_currency}")
    if not ctx.currencies.is_enabled(payload.first_account.currency):
        raise HTTPException(
            400, f"unknown currency: {payload.first_account.currency}"
        )

    try:
        ZoneInfo(payload.timezone)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(400, f"unknown timezone: {payload.timezone}") from exc

    # Re-completing onboarding is idempotent at the user-row level, but we
    # don't want to spam additional accounts / signup bonuses if they tap
    # "complete" twice.
    if user.onboarding_completed:
        raise HTTPException(409, "onboarding already completed")

    await update_user(
        session,
        user,
        language_code=payload.language_code,
        calendar_system=payload.calendar_system,
        timezone=payload.timezone,
        default_currency=payload.default_currency,
    )
    await create_account(
        session,
        user_id=user.telegram_id,
        name=payload.first_account.name,
        type=payload.first_account.type,
        currency=payload.first_account.currency,
        icon=ACCOUNT_TYPE_ICONS[payload.first_account.type],
        is_default=True,
        is_default_income=True,
    )
    await seed_default_categories(
        session, user_id=user.telegram_id, language=payload.language_code
    )

    signup = ctx.app.credits.signup_bonus
    if signup > 0:
        await add_credits(
            session, user=user, amount=signup, reason=CreditReason.SIGNUP_BONUS
        )

    await update_user(session, user, onboarding_completed=True)

    return OnboardingOut(
        onboarding_completed=True,
        credit_balance=user.credit_balance,
        signup_credits_granted=signup,
    )
