"""GET /api/gamification/status — level, xp, streaks, badges."""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.core.bootstrap import load_app_context
from app.models.user import User
from app.services.gamification_service import (
    _get_or_create_xp,
    list_all_badges,
    list_earned_badges,
    list_streaks,
)

router = APIRouter(prefix="/gamification")


class StreakOut(BaseModel):
    streak_type: str
    current_count: int
    best_count: int
    last_activity_date: date | None


class BadgeOut(BaseModel):
    id: str
    name: str
    name_fa: str | None
    description: str
    description_fa: str | None
    icon: str
    xp_reward: int
    earned: bool
    earned_at: datetime | None


class GamificationStatus(BaseModel):
    level: int
    total_xp: int
    xp_into_level: int      # XP earned inside the current level
    xp_for_level: int       # XP needed to complete the current level
    streaks: list[StreakOut]
    badges: list[BadgeOut]


@router.get("/status", response_model=GamificationStatus)
async def get_status(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> GamificationStatus:
    xp_row = await _get_or_create_xp(session, user.telegram_id)
    base = load_app_context().app.gamification.level_xp_base

    xp_at_current_level = (xp_row.level - 1) * base
    xp_into_level = xp_row.total_xp - xp_at_current_level

    streaks = await list_streaks(session, user.telegram_id)
    earned = await list_earned_badges(session, user.telegram_id)
    earned_map = {badge.id: ub for badge, ub in earned}
    all_badges = await list_all_badges(session)

    return GamificationStatus(
        level=xp_row.level,
        total_xp=xp_row.total_xp,
        xp_into_level=xp_into_level,
        xp_for_level=base,
        streaks=[
            StreakOut(
                streak_type=s.streak_type,
                current_count=s.current_count,
                best_count=s.best_count,
                last_activity_date=s.last_activity_date,
            )
            for s in streaks
        ],
        badges=[
            BadgeOut(
                id=b.id,
                name=b.name,
                name_fa=b.name_fa,
                description=b.description,
                description_fa=b.description_fa,
                icon=b.icon,
                xp_reward=b.xp_reward,
                earned=b.id in earned_map,
                earned_at=earned_map[b.id].earned_at if b.id in earned_map else None,
            )
            for b in all_badges
        ],
    )
