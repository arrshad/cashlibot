"""GET /api/categories — list a user's categories."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.models.category import Category, CategoryType
from app.models.user import User
from app.services.category_service import list_categories

router = APIRouter(prefix="/categories")


class CategoryOut(BaseModel):
    id: uuid.UUID
    name: str
    name_en: str
    name_fa: str | None
    type: CategoryType
    icon: str
    color: str | None
    parent_id: uuid.UUID | None

    @classmethod
    def from_model(cls, c: Category) -> "CategoryOut":
        return cls(
            id=c.id,
            name=c.name,
            name_en=c.name_en,
            name_fa=c.name_fa,
            type=c.type,
            icon=c.icon,
            color=c.color,
            parent_id=c.parent_id,
        )


@router.get("", response_model=list[CategoryOut])
async def list_my_categories(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    type: Annotated[CategoryType | None, Query()] = None,
) -> list[CategoryOut]:
    cats = await list_categories(session, user_id=user.telegram_id, type=type)
    return [CategoryOut.from_model(c) for c in cats]
