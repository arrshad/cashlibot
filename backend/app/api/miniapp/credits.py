"""GET /api/credits + POST /api/credits/purchase (Telegram Stars invoice link)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from aiogram import Bot
from aiogram.types import LabeledPrice
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.core.config import get_settings
from app.models.credit import CreditReason, CreditTransaction
from app.models.user import User
from app.services.subscription_service import (
    PACKAGES,
    StarsPackage,
    build_invoice_payload,
    get_package,
)

router = APIRouter(prefix="/credits")

_HISTORY_LIMIT = 30
_STARS_CURRENCY = "XTR"


class CreditPackage(BaseModel):
    id: str
    stars: int
    credits: int
    label: str

    @classmethod
    def from_dataclass(cls, p: StarsPackage) -> "CreditPackage":
        return cls(id=p.id, stars=p.stars, credits=p.credits, label=p.label)


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


class InvoiceLinkOut(BaseModel):
    invoice_link: str


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
        packages=[CreditPackage.from_dataclass(p) for p in PACKAGES],
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


@router.post("/purchase/{package_id}", response_model=InvoiceLinkOut)
async def create_invoice_link(
    package_id: str,
    _user: Annotated[User, Depends(get_current_user)],
) -> InvoiceLinkOut:
    """Return a Telegram Stars invoice URL that the Mini App hands to
    `Telegram.WebApp.openInvoice`. Payment is actually processed by the
    bot's PreCheckoutQuery + SuccessfulPayment handlers — that's where the
    credit ledger is written to, idempotently.
    """
    package = get_package(package_id)
    if package is None:
        raise HTTPException(404, "unknown package")

    settings = get_settings()
    if not settings.telegram_bot_token:
        raise HTTPException(503, "telegram_bot_token not configured")

    bot = Bot(token=settings.telegram_bot_token)
    try:
        link = await bot.create_invoice_link(
            title=f"{package.credits} Cashlibot credits",
            description=(
                f"{package.label} — {package.credits} credits for AI features."
            ),
            payload=build_invoice_payload(package),
            provider_token="",
            currency=_STARS_CURRENCY,
            prices=[
                LabeledPrice(label=f"{package.credits} credits", amount=package.stars)
            ],
        )
    finally:
        await bot.session.close()

    return InvoiceLinkOut(invoice_link=link)
