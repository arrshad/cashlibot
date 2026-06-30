"""Accounts CRUD endpoints for the Mini App."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.api.miniapp.config import ACCOUNT_TYPE_ICONS
from app.core.bootstrap import load_app_context
from app.models.account import Account, AccountType
from app.models.user import User
from app.services.account_service import (
    archive_account,
    create_account,
    get_account,
    list_accounts,
    update_account,
)

router = APIRouter(prefix="/accounts")


class AccountOut(BaseModel):
    id: uuid.UUID
    name: str
    type: AccountType
    currency: str
    current_balance: Decimal
    icon: str
    color: str | None
    is_default: bool
    is_default_income: bool
    is_archived: bool
    created_at: datetime

    @classmethod
    def from_model(cls, a: Account) -> "AccountOut":
        return cls(
            id=a.id,
            name=a.name,
            type=a.type,
            currency=a.currency,
            current_balance=a.current_balance,
            icon=a.icon,
            color=a.color,
            is_default=a.is_default,
            is_default_income=a.is_default_income,
            is_archived=a.is_archived,
            created_at=a.created_at,
        )


class AccountCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    type: AccountType
    currency: str = Field(min_length=2, max_length=5)
    icon: str | None = Field(default=None, max_length=64)
    color: str | None = Field(default=None, max_length=16)
    is_default: bool = False
    is_default_income: bool = False


class AccountPatchIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=40)
    icon: str | None = Field(default=None, max_length=64)
    color: str | None = Field(default=None, max_length=16)
    is_default: bool | None = None
    is_default_income: bool | None = None


@router.get("", response_model=list[AccountOut])
async def list_my_accounts(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    include_archived: Annotated[bool, Query()] = False,
) -> list[AccountOut]:
    accounts = await list_accounts(
        session, user.telegram_id, include_archived=include_archived
    )
    return [AccountOut.from_model(a) for a in accounts]


@router.post("", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
async def create_my_account(
    payload: AccountCreateIn,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AccountOut:
    ctx = load_app_context()
    if not ctx.currencies.is_enabled(payload.currency):
        raise HTTPException(400, f"unknown currency: {payload.currency}")

    icon = payload.icon or ACCOUNT_TYPE_ICONS[payload.type]
    account = await create_account(
        session,
        user_id=user.telegram_id,
        name=payload.name,
        type=payload.type,
        currency=payload.currency,
        icon=icon,
        color=payload.color,
        is_default=payload.is_default,
        is_default_income=payload.is_default_income,
    )
    return AccountOut.from_model(account)


@router.patch("/{account_id}", response_model=AccountOut)
async def update_my_account(
    account_id: uuid.UUID,
    payload: AccountPatchIn,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AccountOut:
    account = await get_account(
        session, account_id=account_id, user_id=user.telegram_id
    )
    if account is None:
        raise HTTPException(404, "account not found")

    fields = payload.model_dump(exclude_unset=True)
    if not fields:
        return AccountOut.from_model(account)

    updated = await update_account(session, account=account, fields=fields)
    return AccountOut.from_model(updated)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_my_account(
    account_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    account = await get_account(
        session, account_id=account_id, user_id=user.telegram_id
    )
    if account is None:
        raise HTTPException(404, "account not found")
    await archive_account(session, account)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
