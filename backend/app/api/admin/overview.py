"""GET /api/admin/overview — top-level KPIs."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.admin.deps import get_admin_session, get_current_admin
from app.models.credit import CreditReason, CreditTransaction
from app.models.stars_purchase import StarsPurchase
from app.models.transaction import Transaction
from app.models.user import User

router = APIRouter()


class OverviewOut(BaseModel):
    total_users: int
    admins: int
    dau: int
    wau: int
    mau: int
    credits_in_circulation: int
    ai_credits_spent_this_month: int
    stars_revenue_this_month: int
    stars_purchases_this_month: int
    credits_granted_via_stars_this_month: int


@router.get("/overview", response_model=OverviewOut)
async def get_overview(
    _admin: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_admin_session)],
) -> OverviewOut:
    total_users = int(
        (await session.execute(select(func.count(User.telegram_id)))).scalar_one()
    )
    admins = int(
        (
            await session.execute(
                select(func.count(User.telegram_id)).where(User.is_admin.is_(True))
            )
        ).scalar_one()
    )
    credits_total = int(
        (
            await session.execute(select(func.coalesce(func.sum(User.credit_balance), 0)))
        ).scalar_one()
    )

    now = datetime.now(UTC)
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # DAU / WAU / MAU: distinct users with at least one non-deleted tx in the
    # window. Cheap enough at our scale to compute on demand.
    async def _active_since(cutoff: datetime) -> int:
        stmt = select(func.count(func.distinct(Transaction.user_id))).where(
            Transaction.is_deleted.is_(False),
            Transaction.created_at >= cutoff,
        )
        return int((await session.execute(stmt)).scalar_one())

    dau = await _active_since(day_ago)
    wau = await _active_since(week_ago)
    mau = await _active_since(month_ago)

    # AI credit spend = sum of |change_amount| over CreditTransaction with
    # reason=AI_USAGE this calendar month (UTC).
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    ai_spend = int(
        (
            await session.execute(
                select(
                    func.coalesce(
                        func.sum(
                            case(
                                (CreditTransaction.change_amount < 0,
                                 -CreditTransaction.change_amount),
                                else_=0,
                            )
                        ),
                        0,
                    )
                ).where(
                    CreditTransaction.reason == CreditReason.AI_USAGE,
                    CreditTransaction.created_at >= month_start,
                )
            )
        ).scalar_one()
    )

    stars_stmt = select(
        func.coalesce(func.sum(StarsPurchase.stars_amount), 0),
        func.count(StarsPurchase.id),
        func.coalesce(func.sum(StarsPurchase.credits_granted), 0),
    ).where(StarsPurchase.created_at >= month_start)
    stars_row = (await session.execute(stars_stmt)).one()

    return OverviewOut(
        total_users=total_users,
        admins=admins,
        dau=dau,
        wau=wau,
        mau=mau,
        credits_in_circulation=credits_total,
        ai_credits_spent_this_month=ai_spend,
        stars_revenue_this_month=int(stars_row[0]),
        stars_purchases_this_month=int(stars_row[1]),
        credits_granted_via_stars_this_month=int(stars_row[2]),
    )
