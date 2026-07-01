"""GET /api/credits — balance, purchase packages, and recent history."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.models.credit import CreditReason, CreditTransaction
from app.models.user import User

router = APIRouter(prefix="/credits")


# Packages the Mini App shows on the "buy more" tab. Purchase happens on the
# bot side via Telegram Stars — the Mini App just displays these tiles until
# the Stars flow lands as its own branch.
_PACKAGES: list[dict[str, int | str]] = [
    {"stars": 50, "credits": 50, "label": "Starter"},
    {"stars": 200, "credits": 220, "label": "Standard"},
    {"stars": 500, "credits": 600, "label": "Plus"},
    {"stars": 1000, "credits": 1300, "label": "Pro"},
]

# How many recent ledger entries to return for the history panel.
_HISTORY_LIMIT = 30


class CreditPackage(BaseModel):
    stars: int
    credits: int
    label: str


class CreditHistoryEntry(BaseModel):
    id: str
    change_amount: int
    balance_after: int
    reason: CreditReason
    reference_id: str | None
    created_at: datetime


class CreditsOut(BaseModel):
    balance: int
    packages: list[CreditPackage]
    history: list[CreditHistoryEntry]


@router.get("", response_model=CreditsOut)
async def get_credits(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CreditsOut:
    stmt = (
        select(CreditTransaction)
        .where(CreditTransaction.user_id == user.telegram_id)
        .order_by(CreditTransaction.created_at.desc())
        .limit(_HISTORY_LIMIT)
    )
    rows = list((await session.execute(stmt)).scalars().all())

    return CreditsOut(
        balance=user.credit_balance,
        packages=[CreditPackage(**p) for p in _PACKAGES],  # type: ignore[arg-type]
        history=[
            CreditHistoryEntry(
                id=str(r.id),
                change_amount=r.change_amount,
                balance_after=r.balance_after,
                reason=r.reason,
                reference_id=r.reference_id,
                created_at=r.created_at,
            )
            for r in rows
        ],
    )
