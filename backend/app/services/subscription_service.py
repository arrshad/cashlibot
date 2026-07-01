"""Telegram Stars packages + idempotent purchase recording."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.credit import CreditReason
from app.models.stars_purchase import StarsPurchase
from app.models.user import User
from app.services.credit_service import add_credits

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class StarsPackage:
    id: str
    stars: int
    credits: int
    label: str


# The single source of truth for what the user can buy. The Mini App reads
# this via GET /api/credits, the bot reads it when rendering /credits and
# when validating pre-checkout, and the ledger record uses `id` as the
# stable identifier so the label / price can drift over time without
# breaking historical rows.
PACKAGES: tuple[StarsPackage, ...] = (
    StarsPackage(id="starter", stars=50, credits=50, label="Starter"),
    StarsPackage(id="standard", stars=200, credits=220, label="Standard"),
    StarsPackage(id="plus", stars=500, credits=600, label="Plus"),
    StarsPackage(id="pro", stars=1000, credits=1300, label="Pro"),
)


def get_package(package_id: str) -> StarsPackage | None:
    return next((p for p in PACKAGES if p.id == package_id), None)


# Payload string carried through Telegram invoice → SuccessfulPayment.
_INVOICE_PAYLOAD_PREFIX = "credits:"


def build_invoice_payload(package: StarsPackage) -> str:
    return f"{_INVOICE_PAYLOAD_PREFIX}{package.id}"


def parse_invoice_payload(payload: str) -> StarsPackage | None:
    if not payload.startswith(_INVOICE_PAYLOAD_PREFIX):
        return None
    return get_package(payload[len(_INVOICE_PAYLOAD_PREFIX) :])


async def record_stars_purchase(
    session: AsyncSession,
    *,
    user: User,
    package: StarsPackage,
    telegram_charge_id: str,
) -> StarsPurchase | None:
    """Grant credits for a successful Stars payment.

    Returns the created row, or `None` if this `telegram_charge_id` was already
    processed — Telegram occasionally re-sends the same success update and we
    never want to double-grant.
    """
    stmt = select(StarsPurchase).where(
        StarsPurchase.telegram_charge_id == telegram_charge_id
    )
    if (await session.execute(stmt)).scalars().first() is not None:
        log.info("stars purchase already recorded: %s", telegram_charge_id)
        return None

    purchase = StarsPurchase(
        user_id=user.telegram_id,
        telegram_charge_id=telegram_charge_id,
        stars_amount=package.stars,
        credits_granted=package.credits,
        package_id=package.id,
    )
    session.add(purchase)
    await add_credits(
        session,
        user=user,
        amount=package.credits,
        reason=CreditReason.STARS_PURCHASE,
        reference_id=telegram_charge_id,
    )
    await session.flush()
    return purchase
