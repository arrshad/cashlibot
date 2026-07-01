"""Dashboard summary endpoint."""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.api.miniapp.transactions import TransactionOut
from app.models.user import User
from app.services.analytics_service import (
    count_active_accounts,
    get_balances_by_currency,
)
from app.services.transaction_service import list_transactions

RECENT_LIMIT = 5

router = APIRouter(prefix="/dashboard")


class CurrencyTotal(BaseModel):
    currency: str
    amount: Decimal


class DashboardSummary(BaseModel):
    totals_by_currency: list[CurrencyTotal]
    account_count: int
    default_currency: str | None
    recent_transactions: list[TransactionOut]


@router.get("/summary", response_model=DashboardSummary)
async def get_summary(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DashboardSummary:
    totals = await get_balances_by_currency(session, user.telegram_id)
    count = await count_active_accounts(session, user.telegram_id)
    recent = await list_transactions(
        session, user_id=user.telegram_id, limit=RECENT_LIMIT, offset=0
    )

    sorted_codes = sorted(
        totals.keys(),
        key=lambda c: (0 if c == user.default_currency else 1, c),
    )
    return DashboardSummary(
        totals_by_currency=[
            CurrencyTotal(currency=c, amount=totals[c]) for c in sorted_codes
        ],
        account_count=count,
        default_currency=user.default_currency,
        recent_transactions=[TransactionOut.from_model(t) for t in recent],
    )
