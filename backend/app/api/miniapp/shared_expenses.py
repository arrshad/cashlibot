"""Shared expenses CRUD + settle + balance."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.core.config import get_settings
from app.i18n import get_i18n
from app.models.shared_expense import (
    SharedExpense,
    SharedExpenseSplit,
    SharedExpenseStatus,
    SplitStatus,
)
from app.models.user import User
from app.services.shared_expense_service import (
    SharedExpenseError,
    SplitInput,
    approve_split,
    create_shared_expense,
    dispute_split,
    get_split,
    list_created_expenses,
    list_expenses_between,
    list_pending_splits_for,
    list_splits_for_expense,
    net_balance_with,
    settle_with_friend,
)

log = logging.getLogger(__name__)
router = APIRouter(prefix="/shared-expenses")


# ---------- Schemas ----------


class SplitIn(BaseModel):
    user_id: int
    amount_owed: Decimal = Field(gt=Decimal(0))


class SharedExpenseCreateIn(BaseModel):
    description: str = Field(min_length=1, max_length=200)
    total_amount: Decimal = Field(gt=Decimal(0))
    currency: str = Field(min_length=2, max_length=5)
    splits: list[SplitIn] = Field(min_length=1)


class SplitOut(BaseModel):
    id: uuid.UUID
    shared_expense_id: uuid.UUID
    user_id: int
    amount_owed: Decimal
    status: SplitStatus
    approved_at: datetime | None
    settled_at: datetime | None

    @classmethod
    def from_model(cls, s: SharedExpenseSplit) -> "SplitOut":
        return cls(
            id=s.id,
            shared_expense_id=s.shared_expense_id,
            user_id=s.user_id,
            amount_owed=s.amount_owed,
            status=s.status,
            approved_at=s.approved_at,
            settled_at=s.settled_at,
        )


class SharedExpenseOut(BaseModel):
    id: uuid.UUID
    created_by_user_id: int
    description: str
    total_amount: Decimal
    currency: str
    status: SharedExpenseStatus
    created_at: datetime
    splits: list[SplitOut]

    @classmethod
    def from_model(
        cls, e: SharedExpense, splits: list[SharedExpenseSplit]
    ) -> "SharedExpenseOut":
        return cls(
            id=e.id,
            created_by_user_id=e.created_by_user_id,
            description=e.description,
            total_amount=e.total_amount,
            currency=e.currency,
            status=e.status,
            created_at=e.created_at,
            splits=[SplitOut.from_model(s) for s in splits],
        )


class SharedExpensesOverview(BaseModel):
    pending_my_approval: list[SplitOut]
    created_by_me: list[SharedExpenseOut]


class CurrencyBalance(BaseModel):
    currency: str
    amount: Decimal   # signed; + means friend owes me, - means I owe friend


class FriendBalance(BaseModel):
    friend_id: int
    per_currency: list[CurrencyBalance]
    expenses: list[SharedExpenseOut]


class SettleOut(BaseModel):
    splits_settled: int


# ---------- Endpoints ----------


@router.get("", response_model=SharedExpensesOverview)
async def get_overview(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SharedExpensesOverview:
    pending = await list_pending_splits_for(session, user.telegram_id)
    created = await list_created_expenses(session, user.telegram_id)
    created_out: list[SharedExpenseOut] = []
    for expense in created:
        splits = await list_splits_for_expense(session, expense.id)
        created_out.append(SharedExpenseOut.from_model(expense, splits))
    return SharedExpensesOverview(
        pending_my_approval=[SplitOut.from_model(s) for s in pending],
        created_by_me=created_out,
    )


@router.post(
    "", response_model=SharedExpenseOut, status_code=status.HTTP_201_CREATED
)
async def create(
    payload: SharedExpenseCreateIn,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SharedExpenseOut:
    try:
        expense, splits = await create_shared_expense(
            session,
            creator=user,
            description=payload.description,
            total_amount=payload.total_amount,
            currency=payload.currency,
            splits=[
                SplitInput(user_id=s.user_id, amount_owed=s.amount_owed)
                for s in payload.splits
            ],
        )
    except SharedExpenseError as exc:
        raise HTTPException(400, str(exc)) from exc

    # Fire off DMs to each debtor. Failures are logged but non-fatal — the
    # expense is created regardless.
    await _notify_participants(session, creator=user, expense=expense, splits=splits)

    return SharedExpenseOut.from_model(expense, splits)


@router.post(
    "/splits/{split_id}/approve", response_model=SplitOut
)
async def approve(
    split_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SplitOut:
    split = await get_split(session, split_id)
    if split is None:
        raise HTTPException(404, "split not found")
    try:
        split = await approve_split(session, split=split, actor=user)
    except SharedExpenseError as exc:
        raise HTTPException(400, str(exc)) from exc
    return SplitOut.from_model(split)


@router.post(
    "/splits/{split_id}/dispute", response_model=SplitOut
)
async def dispute(
    split_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SplitOut:
    split = await get_split(session, split_id)
    if split is None:
        raise HTTPException(404, "split not found")
    try:
        split = await dispute_split(session, split=split, actor=user)
    except SharedExpenseError as exc:
        raise HTTPException(400, str(exc)) from exc
    return SplitOut.from_model(split)


@router.get(
    "/friends/{friend_id}/balance", response_model=FriendBalance
)
async def get_balance(
    friend_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> FriendBalance:
    balances = await net_balance_with(
        session, viewer_id=user.telegram_id, friend_id=friend_id
    )
    pairs = await list_expenses_between(session, user.telegram_id, friend_id)

    # Group splits under their expense so the client renders one row per
    # expense with all splits attached.
    seen: dict[uuid.UUID, SharedExpense] = {}
    for expense, _ in pairs:
        seen.setdefault(expense.id, expense)
    expense_outs: list[SharedExpenseOut] = []
    for expense_id, expense in seen.items():
        splits = await list_splits_for_expense(session, expense_id)
        expense_outs.append(SharedExpenseOut.from_model(expense, splits))
    expense_outs.sort(key=lambda e: e.created_at, reverse=True)

    return FriendBalance(
        friend_id=friend_id,
        per_currency=[
            CurrencyBalance(currency=c, amount=a)
            for c, a in balances.per_currency.items()
        ],
        expenses=expense_outs,
    )


@router.post(
    "/friends/{friend_id}/settle", response_model=SettleOut
)
async def settle(
    friend_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SettleOut:
    count = await settle_with_friend(
        session, viewer_id=user.telegram_id, friend_id=friend_id
    )
    return SettleOut(splits_settled=count)


# ---------- Notifications ----------


async def _notify_participants(
    session: AsyncSession,
    *,
    creator: User,
    expense: SharedExpense,
    splits: list[SharedExpenseSplit],
) -> None:
    settings = get_settings()
    if not settings.telegram_bot_token:
        log.info("skipping split notifications — no telegram_bot_token set")
        return

    bot = Bot(token=settings.telegram_bot_token)
    i18n = get_i18n()
    try:
        for split in splits:
            debtor = await session.get(User, split.user_id)
            if debtor is None:
                continue
            lang = debtor.language_code
            body = i18n.t(
                lang,
                "shared_expense.incoming_split",
                creator_name=creator.display_name,
                description=expense.description,
                amount=str(split.amount_owed),
                currency=expense.currency,
            )
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=i18n.t(lang, "shared_expense.button.approve"),
                            callback_data=f"split:approve:{split.id}",
                        ),
                        InlineKeyboardButton(
                            text=i18n.t(lang, "shared_expense.button.dispute"),
                            callback_data=f"split:dispute:{split.id}",
                        ),
                    ]
                ]
            )
            try:
                await bot.send_message(
                    chat_id=debtor.telegram_id,
                    text=body,
                    reply_markup=keyboard,
                )
            except (TelegramForbiddenError, TelegramBadRequest) as exc:
                log.info(
                    "shared_expense: couldn't DM %s (%s)", debtor.telegram_id, exc
                )
    finally:
        await bot.session.close()
