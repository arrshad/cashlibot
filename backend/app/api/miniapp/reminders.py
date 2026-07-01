"""Reminders CRUD."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.models.frequency import Frequency
from app.models.reminder import Reminder, ReminderType
from app.models.user import User
from app.services.reminder_service import (
    ReminderError,
    create_reminder,
    delete_reminder,
    get_reminder,
    list_reminders,
    update_reminder,
)

router = APIRouter(prefix="/reminders")


class ReminderOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    reminder_type: ReminderType
    due_at: datetime
    repeat_frequency: Frequency | None
    is_active: bool
    last_fired_at: datetime | None
    created_at: datetime

    @classmethod
    def from_model(cls, r: Reminder) -> "ReminderOut":
        return cls(
            id=r.id,
            title=r.title,
            description=r.description,
            reminder_type=r.reminder_type,
            due_at=r.due_at,
            repeat_frequency=r.repeat_frequency,
            is_active=r.is_active,
            last_fired_at=r.last_fired_at,
            created_at=r.created_at,
        )


class ReminderCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    reminder_type: ReminderType = ReminderType.CUSTOM
    due_at: datetime
    repeat_frequency: Frequency | None = None


class ReminderPatchIn(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    due_at: datetime | None = None
    repeat_frequency: Frequency | None = None
    is_active: bool | None = None


@router.get("", response_model=list[ReminderOut])
async def list_my_reminders(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    include_inactive: bool = False,
) -> list[ReminderOut]:
    rows = await list_reminders(
        session, user.telegram_id, include_inactive=include_inactive
    )
    return [ReminderOut.from_model(r) for r in rows]


@router.post("", response_model=ReminderOut, status_code=status.HTTP_201_CREATED)
async def create_my_reminder(
    payload: ReminderCreateIn,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ReminderOut:
    try:
        reminder = await create_reminder(
            session,
            user_id=user.telegram_id,
            title=payload.title,
            description=payload.description,
            reminder_type=payload.reminder_type,
            due_at=payload.due_at,
            repeat_frequency=payload.repeat_frequency,
        )
    except ReminderError as exc:
        raise HTTPException(400, str(exc)) from exc
    return ReminderOut.from_model(reminder)


@router.patch("/{reminder_id}", response_model=ReminderOut)
async def update_my_reminder(
    reminder_id: uuid.UUID,
    payload: ReminderPatchIn,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ReminderOut:
    reminder = await get_reminder(
        session, reminder_id=reminder_id, user_id=user.telegram_id
    )
    if reminder is None:
        raise HTTPException(404, "reminder not found")
    fields = payload.model_dump(exclude_unset=True)
    if not fields:
        return ReminderOut.from_model(reminder)
    try:
        updated = await update_reminder(session, reminder=reminder, fields=fields)
    except ReminderError as exc:
        raise HTTPException(400, str(exc)) from exc
    return ReminderOut.from_model(updated)


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_reminder(
    reminder_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    reminder = await get_reminder(
        session, reminder_id=reminder_id, user_id=user.telegram_id
    )
    if reminder is None:
        raise HTTPException(404, "reminder not found")
    await delete_reminder(session, reminder)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
