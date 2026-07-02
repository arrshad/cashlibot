"""Admin: list users, user detail, adjust credits."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.admin.deps import get_admin_session, get_current_admin
from app.core.exceptions import InsufficientCreditsError
from app.models.credit import CreditReason, CreditTransaction
from app.models.transaction import Transaction
from app.models.user import User
from app.services.credit_service import add_credits, deduct_credits

router = APIRouter(prefix="/users")


class UserRow(BaseModel):
    telegram_id: int
    username: str | None
    display_name: str
    language_code: str
    default_currency: str | None
    credit_balance: int
    is_admin: bool
    onboarding_completed: bool
    created_at: datetime
    last_tx_at: datetime | None
    tx_count: int


class UserListOut(BaseModel):
    total: int
    limit: int
    offset: int
    rows: list[UserRow]


class CreditHistoryRow(BaseModel):
    id: str
    change_amount: int
    balance_after: int
    reason: CreditReason
    reference_id: str | None
    created_at: datetime


class UserDetailOut(UserRow):
    credit_history: list[CreditHistoryRow]


class CreditAdjustIn(BaseModel):
    change: int = Field(description="positive to grant, negative to deduct; non-zero")
    reference: str | None = Field(default=None, max_length=200)


@router.get("", response_model=UserListOut)
async def list_users(
    _admin: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_admin_session)],
    q: Annotated[str | None, Query(description="username or display-name search")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> UserListOut:
    base = select(User)
    if q:
        like = f"%{q.strip().lower()}%"
        base = base.where(
            or_(
                func.lower(User.username).like(like),
                func.lower(User.display_name).like(like),
            )
        )

    total = int(
        (
            await session.execute(
                select(func.count()).select_from(base.subquery())
            )
        ).scalar_one()
    )
    rows = list(
        (
            await session.execute(
                base.order_by(User.created_at.desc()).limit(limit).offset(offset)
            )
        )
        .scalars()
        .all()
    )

    # One activity summary query per page (small), avoids an N+1.
    ids = [u.telegram_id for u in rows]
    if ids:
        agg_stmt = (
            select(
                Transaction.user_id,
                func.count().label("cnt"),
                func.max(Transaction.created_at).label("last_at"),
            )
            .where(Transaction.user_id.in_(ids), Transaction.is_deleted.is_(False))
            .group_by(Transaction.user_id)
        )
        agg = {r[0]: (int(r[1]), r[2]) for r in (await session.execute(agg_stmt)).all()}
    else:
        agg = {}

    return UserListOut(
        total=total,
        limit=limit,
        offset=offset,
        rows=[
            UserRow(
                telegram_id=u.telegram_id,
                username=u.username,
                display_name=u.display_name,
                language_code=u.language_code,
                default_currency=u.default_currency,
                credit_balance=u.credit_balance,
                is_admin=u.is_admin,
                onboarding_completed=u.onboarding_completed,
                created_at=u.created_at,
                last_tx_at=agg.get(u.telegram_id, (0, None))[1],
                tx_count=agg.get(u.telegram_id, (0, None))[0],
            )
            for u in rows
        ],
    )


async def _load_user_or_404(session: AsyncSession, user_id: int) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(404, "user not found")
    return user


@router.get("/{user_id}", response_model=UserDetailOut)
async def get_user(
    user_id: int,
    _admin: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_admin_session)],
) -> UserDetailOut:
    user = await _load_user_or_404(session, user_id)

    stmt = (
        select(CreditTransaction)
        .where(CreditTransaction.user_id == user_id)
        .order_by(CreditTransaction.created_at.desc())
        .limit(30)
    )
    history = list((await session.execute(stmt)).scalars().all())

    tx_stmt = select(
        func.count().label("cnt"),
        func.max(Transaction.created_at).label("last_at"),
    ).where(
        Transaction.user_id == user_id, Transaction.is_deleted.is_(False)
    )
    tx_agg = (await session.execute(tx_stmt)).one()

    return UserDetailOut(
        telegram_id=user.telegram_id,
        username=user.username,
        display_name=user.display_name,
        language_code=user.language_code,
        default_currency=user.default_currency,
        credit_balance=user.credit_balance,
        is_admin=user.is_admin,
        onboarding_completed=user.onboarding_completed,
        created_at=user.created_at,
        last_tx_at=tx_agg[1],
        tx_count=int(tx_agg[0]),
        credit_history=[
            CreditHistoryRow(
                id=str(h.id),
                change_amount=h.change_amount,
                balance_after=h.balance_after,
                reason=h.reason,
                reference_id=h.reference_id,
                created_at=h.created_at,
            )
            for h in history
        ],
    )


@router.post(
    "/{user_id}/credits",
    response_model=UserDetailOut,
    status_code=status.HTTP_200_OK,
)
async def adjust_credits(
    user_id: int,
    payload: CreditAdjustIn,
    _admin: Annotated[User, Depends(get_current_admin)],
    session: Annotated[AsyncSession, Depends(get_admin_session)],
) -> UserDetailOut:
    if payload.change == 0:
        raise HTTPException(400, "change must be non-zero")

    user = await _load_user_or_404(session, user_id)

    if payload.change > 0:
        await add_credits(
            session,
            user=user,
            amount=payload.change,
            reason=CreditReason.ADMIN_ADJUSTMENT,
            reference_id=payload.reference,
        )
    else:
        try:
            await deduct_credits(
                session,
                user=user,
                amount=-payload.change,
                reason=CreditReason.ADMIN_ADJUSTMENT,
                reference_id=payload.reference,
            )
        except InsufficientCreditsError as exc:
            raise HTTPException(400, str(exc)) from exc

    return await get_user(user_id, _admin, session)
