"""Friends CRUD for the Mini App."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.models.friendship import Friendship, FriendshipStatus
from app.models.user import User
from app.services.friend_service import (
    FriendError,
    accept as accept_friend,
    counterpart_id,
    decline as decline_friend,
    get_friendship,
    list_friends,
    list_pending_incoming,
    list_pending_outgoing,
    send_request,
)
from app.services.gamification_service import award_badge

router = APIRouter(prefix="/friends")


class FriendPeer(BaseModel):
    """Compact snapshot of the "other" user in a friendship row."""
    telegram_id: int
    username: str | None
    display_name: str


class FriendshipOut(BaseModel):
    id: uuid.UUID
    status: FriendshipStatus
    peer: FriendPeer
    direction: str  # "incoming" | "outgoing" | "mutual"
    created_at: datetime
    updated_at: datetime


class FriendsOverview(BaseModel):
    accepted: list[FriendshipOut]
    incoming: list[FriendshipOut]
    outgoing: list[FriendshipOut]


class FriendRequestIn(BaseModel):
    username: str = Field(min_length=1, max_length=64)


async def _hydrate(
    session: AsyncSession, friendship: Friendship, viewer_id: int
) -> FriendshipOut:
    peer_id = counterpart_id(friendship, viewer_id)
    peer = await session.get(User, peer_id)
    peer_snapshot = FriendPeer(
        telegram_id=peer_id,
        username=peer.username if peer else None,
        display_name=peer.display_name if peer else str(peer_id),
    )
    if friendship.status == FriendshipStatus.ACCEPTED:
        direction = "mutual"
    elif friendship.addressee_id == viewer_id:
        direction = "incoming"
    else:
        direction = "outgoing"
    return FriendshipOut(
        id=friendship.id,
        status=friendship.status,
        peer=peer_snapshot,
        direction=direction,
        created_at=friendship.created_at,
        updated_at=friendship.updated_at,
    )


@router.get("", response_model=FriendsOverview)
async def get_friends_overview(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> FriendsOverview:
    accepted = await list_friends(session, user.telegram_id)
    incoming = await list_pending_incoming(session, user.telegram_id)
    outgoing = await list_pending_outgoing(session, user.telegram_id)
    return FriendsOverview(
        accepted=[await _hydrate(session, f, user.telegram_id) for f in accepted],
        incoming=[await _hydrate(session, f, user.telegram_id) for f in incoming],
        outgoing=[await _hydrate(session, f, user.telegram_id) for f in outgoing],
    )


@router.post(
    "", response_model=FriendshipOut, status_code=status.HTTP_201_CREATED
)
async def create_friend_request(
    payload: FriendRequestIn,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> FriendshipOut:
    try:
        friendship = await send_request(
            session, requester=user, addressee_username=payload.username
        )
    except FriendError as exc:
        raise HTTPException(400, str(exc)) from exc
    return await _hydrate(session, friendship, user.telegram_id)


@router.post("/{friendship_id}/accept", response_model=FriendshipOut)
async def accept_friend_request(
    friendship_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> FriendshipOut:
    friendship = await get_friendship(session, friendship_id=friendship_id)
    if friendship is None:
        raise HTTPException(404, "friendship not found")
    try:
        friendship = await accept_friend(
            session, friendship=friendship, accepting_user=user
        )
    except FriendError as exc:
        raise HTTPException(400, str(exc)) from exc

    # Idempotent friend_added badge for both users.
    await award_badge(session, user_id=user.telegram_id, badge_id="friend_added")
    await award_badge(
        session, user_id=friendship.requester_id, badge_id="friend_added"
    )

    return await _hydrate(session, friendship, user.telegram_id)


@router.post("/{friendship_id}/decline", response_model=FriendshipOut)
async def decline_friend_request(
    friendship_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> FriendshipOut:
    friendship = await get_friendship(session, friendship_id=friendship_id)
    if friendship is None:
        raise HTTPException(404, "friendship not found")
    try:
        friendship = await decline_friend(
            session, friendship=friendship, declining_user=user
        )
    except FriendError as exc:
        raise HTTPException(400, str(exc)) from exc
    return await _hydrate(session, friendship, user.telegram_id)
