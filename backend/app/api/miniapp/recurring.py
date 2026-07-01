"""Recurring templates CRUD."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.models.frequency import Frequency
from app.models.recurring import RecurringTemplate
from app.models.user import User
from app.services.recurring_service import (
    RecurringError,
    create_template,
    delete_template,
    get_template,
    list_templates,
)

router = APIRouter(prefix="/recurring")


class RecurringOut(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    category_id: uuid.UUID
    amount: Decimal
    currency: str
    description: str
    frequency: Frequency
    next_due_date: date
    is_active: bool
    created_at: datetime

    @classmethod
    def from_model(cls, t: RecurringTemplate) -> "RecurringOut":
        return cls(
            id=t.id,
            account_id=t.account_id,
            category_id=t.category_id,
            amount=t.amount,
            currency=t.currency,
            description=t.description,
            frequency=t.frequency,
            next_due_date=t.next_due_date,
            is_active=t.is_active,
            created_at=t.created_at,
        )


class RecurringCreateIn(BaseModel):
    account_id: uuid.UUID
    category_id: uuid.UUID
    amount: Decimal = Field(gt=Decimal(0))
    description: str = Field(min_length=1, max_length=200)
    frequency: Frequency
    next_due_date: date


@router.get("", response_model=list[RecurringOut])
async def list_my_recurring(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[RecurringOut]:
    templates = await list_templates(session, user.telegram_id)
    return [RecurringOut.from_model(t) for t in templates]


@router.post(
    "", response_model=RecurringOut, status_code=status.HTTP_201_CREATED
)
async def create_my_recurring(
    payload: RecurringCreateIn,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RecurringOut:
    try:
        template = await create_template(
            session,
            user_id=user.telegram_id,
            account_id=payload.account_id,
            category_id=payload.category_id,
            amount=payload.amount,
            description=payload.description,
            frequency=payload.frequency,
            next_due_date=payload.next_due_date,
        )
    except RecurringError as exc:
        raise HTTPException(400, str(exc)) from exc
    return RecurringOut.from_model(template)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_recurring(
    template_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    template = await get_template(
        session, template_id=template_id, user_id=user.telegram_id
    )
    if template is None:
        raise HTTPException(404, "template not found")
    await delete_template(session, template)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
