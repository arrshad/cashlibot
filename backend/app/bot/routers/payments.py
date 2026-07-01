"""/credits command + Telegram Stars invoice + success flow."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)

from app.core.db import session_scope
from app.i18n import get_i18n
from app.models.user import User
from app.services.subscription_service import (
    PACKAGES,
    build_invoice_payload,
    get_package,
    parse_invoice_payload,
    record_stars_purchase,
)

log = logging.getLogger(__name__)
router = Router(name="payments")

_STARS_CURRENCY = "XTR"


def _packages_keyboard(lang: str, i18n) -> InlineKeyboardMarkup:
    rows = []
    for p in PACKAGES:
        rows.append(
            [
                InlineKeyboardButton(
                    text=i18n.t(
                        lang,
                        "credits.package_button",
                        label=p.label,
                        credits=p.credits,
                        stars=p.stars,
                    ),
                    callback_data=f"buy:{p.id}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(Command("credits"))
async def show_credits(message: Message) -> None:
    tg_user = message.from_user
    if tg_user is None:
        return

    i18n = get_i18n()
    async with session_scope() as session:
        user = await session.get(User, tg_user.id)
    lang = user.language_code if user else "en"
    balance = user.credit_balance if user else 0

    await message.answer(
        i18n.t(lang, "credits.balance_and_pick", balance=balance),
        reply_markup=_packages_keyboard(lang, i18n),
    )


@router.callback_query(F.data.startswith("buy:"))
async def send_invoice_for_package(cb: CallbackQuery) -> None:
    if cb.from_user is None or cb.message is None or not cb.data:
        await cb.answer()
        return

    _, _, package_id = cb.data.partition(":")
    package = get_package(package_id)
    if package is None:
        await cb.answer("Unknown package", show_alert=True)
        return

    i18n = get_i18n()
    async with session_scope() as session:
        user = await session.get(User, cb.from_user.id)
    lang = user.language_code if user else "en"

    await cb.answer()
    await cb.bot.send_invoice(
        chat_id=cb.from_user.id,
        title=i18n.t(lang, "credits.invoice_title", credits=package.credits),
        description=i18n.t(
            lang,
            "credits.invoice_description",
            label=package.label,
            credits=package.credits,
        ),
        payload=build_invoice_payload(package),
        provider_token="",
        currency=_STARS_CURRENCY,
        prices=[LabeledPrice(label=f"{package.credits} credits", amount=package.stars)],
    )


@router.pre_checkout_query()
async def on_pre_checkout(query: PreCheckoutQuery) -> None:
    """Telegram calls this right before charging the user. Validate the payload
    against our package list — anything unknown is rejected so the payment
    never completes."""
    package = parse_invoice_payload(query.invoice_payload)
    if package is None:
        log.warning("pre_checkout: unknown payload %r", query.invoice_payload)
        await query.answer(ok=False, error_message="This item is no longer available.")
        return
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def on_successful_payment(message: Message) -> None:
    sp = message.successful_payment
    tg_user = message.from_user
    if sp is None or tg_user is None:
        return

    package = parse_invoice_payload(sp.invoice_payload)
    if package is None:
        log.warning(
            "successful_payment with unrecognised payload %r", sp.invoice_payload
        )
        return

    i18n = get_i18n()

    async with session_scope() as session:
        user = await session.get(User, tg_user.id)
        if user is None:
            log.warning("successful_payment for unknown user %s", tg_user.id)
            return

        lang = user.language_code
        purchase = await record_stars_purchase(
            session,
            user=user,
            package=package,
            telegram_charge_id=sp.telegram_payment_charge_id,
        )
        new_balance = user.credit_balance

    if purchase is None:
        # Duplicate SuccessfulPayment — we already granted credits earlier.
        # Reply anyway so the user sees a confirmation, but skip the balance
        # message (their balance didn't change on this delivery).
        await message.answer(i18n.t(lang, "credits.paid_duplicate"))
        return

    await message.answer(
        i18n.t(
            lang,
            "credits.paid",
            credits=package.credits,
            balance=new_balance,
        )
    )
