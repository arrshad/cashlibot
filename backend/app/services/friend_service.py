"""Friendships: send request, accept, decline, list."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.bootstrap import load_app_context
from app.models.credit import CreditReason
from app.models.friendship import Friendship, FriendshipStatus
from app.models.user import User
from app.services.credit_service import add_credits


class FriendError(ValueError):
    """User-facing error (unknown user, self-request, duplicate, etc.)."""


# ---------- Lookup helpers ----------


async def find_user_by_username(
    session: AsyncSession, username: str
) -> User | None:
    """Case-insensitive lookup. Strips a leading @ so the caller can pass
    either form."""
    handle = username.strip().lstrip("@")
    if not handle:
        return None
    stmt = select(User).where(func.lower(User.username) == handle.lower())
    return (await session.execute(stmt)).scalars().first()


async def get_friendship_between(
    session: AsyncSession, *, user_a: int, user_b: int
) -> Friendship | None:
    """Return the current (pending / accepted / declined) friendship row
    between two users, in either direction. Newest wins if there are stale
    declined rows sitting around."""
    stmt = (
        select(Friendship)
        .where(
            or_(
                (Friendship.requester_id == user_a)
                & (Friendship.addressee_id == user_b),
                (Friendship.requester_id == user_b)
                & (Friendship.addressee_id == user_a),
            )
        )
        .order_by(Friendship.updated_at.desc())
    )
    return (await session.execute(stmt)).scalars().first()


# ---------- Actions ----------


async def send_request(
    session: AsyncSession, *, requester: User, addressee_username: str
) -> Friendship:
    addressee = await find_user_by_username(session, addressee_username)
    if addressee is None:
        raise FriendError("no user with that username")
    if addressee.telegram_id == requester.telegram_id:
        raise FriendError("can't friend yourself")

    existing = await get_friendship_between(
        session, user_a=requester.telegram_id, user_b=addressee.telegram_id
    )
    if existing and existing.status == FriendshipStatus.ACCEPTED:
        raise FriendError("already friends")
    if existing and existing.status == FriendshipStatus.PENDING:
        raise FriendError("a request between you two is already pending")

    friendship = Friendship(
        requester_id=requester.telegram_id,
        addressee_id=addressee.telegram_id,
        status=FriendshipStatus.PENDING,
    )
    session.add(friendship)
    try:
        await session.flush()
    except IntegrityError as exc:  # partial unique index race
        raise FriendError("a request between you two is already pending") from exc
    return friendship


async def accept(
    session: AsyncSession, *, friendship: Friendship, accepting_user: User
) -> Friendship:
    if friendship.addressee_id != accepting_user.telegram_id:
        raise FriendError("only the addressee can accept this request")
    if friendship.status != FriendshipStatus.PENDING:
        raise FriendError("this request isn't pending")

    friendship.status = FriendshipStatus.ACCEPTED
    friendship.updated_at = datetime.now(UTC)
    session.add(friendship)

    # Grant the config-driven bonus to both participants.
    bonus = load_app_context().app.credits.friend_add_bonus
    if bonus > 0:
        requester = await session.get(User, friendship.requester_id)
        if requester is not None:
            await add_credits(
                session,
                user=requester,
                amount=bonus,
                reason=CreditReason.FRIEND_BONUS,
                reference_id=str(friendship.id),
            )
        await add_credits(
            session,
            user=accepting_user,
            amount=bonus,
            reason=CreditReason.FRIEND_BONUS,
            reference_id=str(friendship.id),
        )

    await session.flush()
    return friendship


async def decline(
    session: AsyncSession, *, friendship: Friendship, declining_user: User
) -> Friendship:
    if friendship.addressee_id != declining_user.telegram_id:
        raise FriendError("only the addressee can decline this request")
    if friendship.status != FriendshipStatus.PENDING:
        raise FriendError("this request isn't pending")
    friendship.status = FriendshipStatus.DECLINED
    friendship.updated_at = datetime.now(UTC)
    session.add(friendship)
    await session.flush()
    return friendship


# ---------- Listing ----------


async def list_friends(session: AsyncSession, user_id: int) -> list[Friendship]:
    stmt = select(Friendship).where(
        (
            (Friendship.requester_id == user_id)
            | (Friendship.addressee_id == user_id)
        )
        & (Friendship.status == FriendshipStatus.ACCEPTED)
    )
    return list((await session.execute(stmt)).scalars().all())


async def list_pending_incoming(
    session: AsyncSession, user_id: int
) -> list[Friendship]:
    stmt = select(Friendship).where(
        Friendship.addressee_id == user_id,
        Friendship.status == FriendshipStatus.PENDING,
    )
    return list((await session.execute(stmt)).scalars().all())


async def list_pending_outgoing(
    session: AsyncSession, user_id: int
) -> list[Friendship]:
    stmt = select(Friendship).where(
        Friendship.requester_id == user_id,
        Friendship.status == FriendshipStatus.PENDING,
    )
    return list((await session.execute(stmt)).scalars().all())


def counterpart_id(friendship: Friendship, viewer_id: int) -> int:
    """Return the *other* user's id from the viewer's perspective."""
    return (
        friendship.addressee_id
        if friendship.requester_id == viewer_id
        else friendship.requester_id
    )


async def load_counterpart(
    session: AsyncSession, friendship: Friendship, viewer_id: int
) -> User | None:
    return await session.get(User, counterpart_id(friendship, viewer_id))


async def get_friendship(
    session: AsyncSession, *, friendship_id: uuid.UUID
) -> Friendship | None:
    return await session.get(Friendship, friendship_id)
