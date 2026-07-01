"""Transactions CRUD."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.models.transaction import Transaction, TransactionSource, TransactionType
from app.models.user import User
from app.services.gamification_service import on_transaction_created
from app.services.transaction_service import (
    TransactionError,
    create_transaction,
    delete_transaction,
    get_transaction,
    list_transactions,
    update_transaction,
)

router = APIRouter(prefix="/transactions")


class TransactionOut(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    to_account_id: uuid.UUID | None
    category_id: uuid.UUID | None
    type: TransactionType
    amount: Decimal
    currency: str
    merchant: str | None
    description: str | None
    occurred_at: datetime
    source: TransactionSource
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, tx: Transaction) -> "TransactionOut":
        return cls(
            id=tx.id,
            account_id=tx.account_id,
            to_account_id=tx.to_account_id,
            category_id=tx.category_id,
            type=tx.type,
            amount=tx.amount,
            currency=tx.currency,
            merchant=tx.merchant,
            description=tx.description,
            occurred_at=tx.occurred_at,
            source=tx.source,
            created_at=tx.created_at,
            updated_at=tx.updated_at,
        )


class TransactionCreateIn(BaseModel):
    type: TransactionType
    account_id: uuid.UUID
    amount: Decimal = Field(gt=Decimal(0))
    occurred_at: datetime
    to_account_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    merchant: str | None = Field(default=None, max_length=128)
    description: str | None = Field(default=None, max_length=500)


class TransactionPatchIn(BaseModel):
    type: TransactionType | None = None
    account_id: uuid.UUID | None = None
    to_account_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    amount: Decimal | None = Field(default=None, gt=Decimal(0))
    occurred_at: datetime | None = None
    merchant: str | None = Field(default=None, max_length=128)
    description: str | None = Field(default=None, max_length=500)


@router.get("", response_model=list[TransactionOut])
async def list_my_transactions(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    account_id: Annotated[uuid.UUID | None, Query()] = None,
    category_id: Annotated[uuid.UUID | None, Query()] = None,
    type: Annotated[TransactionType | None, Query()] = None,
    start: Annotated[datetime | None, Query()] = None,
    end: Annotated[datetime | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[TransactionOut]:
    txs = await list_transactions(
        session,
        user_id=user.telegram_id,
        account_id=account_id,
        category_id=category_id,
        type=type,
        start=start,
        end=end,
        limit=limit,
        offset=offset,
    )
    return [TransactionOut.from_model(t) for t in txs]


@router.post(
    "", response_model=TransactionOut, status_code=status.HTTP_201_CREATED
)
async def create_my_transaction(
    payload: TransactionCreateIn,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TransactionOut:
    try:
        tx = await create_transaction(
            session,
            user_id=user.telegram_id,
            type=payload.type,
            account_id=payload.account_id,
            amount=payload.amount,
            occurred_at=payload.occurred_at,
            to_account_id=payload.to_account_id,
            category_id=payload.category_id,
            merchant=payload.merchant,
            description=payload.description,
        )
    except TransactionError as exc:
        raise HTTPException(400, str(exc)) from exc

    # Gamification runs after the tx is in the DB. Events are swallowed here
    # (the Mini App refreshes its own stats when the user opens the screen);
    # the bot preview handler surfaces them as chat messages instead.
    await on_transaction_created(
        session,
        user_id=user.telegram_id,
        source=tx.source,
        tz_name=user.timezone,
    )

    return TransactionOut.from_model(tx)


@router.patch("/{transaction_id}", response_model=TransactionOut)
async def update_my_transaction(
    transaction_id: uuid.UUID,
    payload: TransactionPatchIn,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TransactionOut:
    tx = await get_transaction(
        session, transaction_id=transaction_id, user_id=user.telegram_id
    )
    if tx is None:
        raise HTTPException(404, "transaction not found")

    fields = payload.model_dump(exclude_unset=True)
    if not fields:
        return TransactionOut.from_model(tx)

    try:
        updated = await update_transaction(session, tx=tx, fields=fields)
    except TransactionError as exc:
        raise HTTPException(400, str(exc)) from exc
    return TransactionOut.from_model(updated)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_transaction(
    transaction_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    tx = await get_transaction(
        session, transaction_id=transaction_id, user_id=user.telegram_id
    )
    if tx is None:
        raise HTTPException(404, "transaction not found")
    await delete_transaction(session, tx)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
