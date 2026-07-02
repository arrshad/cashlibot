"""/friends and /addfriend commands + accept/decline callbacks."""

from __future__ import annotations

import logging
import uuid

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.core.db import session_scope
from app.i18n import get_i18n
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

log = logging.getLogger(__name__)
router = Router(name="friends")


def _accept_decline_kb(lang: str, i18n, friendship_id: uuid.UUID) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.t(lang, "friends.button.accept"),
                    callback_data=f"friend:accept:{friendship_id}",
                ),
                InlineKeyboardButton(
                    text=i18n.t(lang, "friends.button.decline"),
                    callback_data=f"friend:decline:{friendship_id}",
                ),
            ]
        ]
    )


@router.message(Command("addfriend"))
async def cmd_add_friend(message: Message, command: CommandObject) -> None:
    if message.from_user is None:
        return
    handle = (command.args or "").strip()
    i18n = get_i18n()

    async with session_scope() as session:
        me = await session.get(User, message.from_user.id)
        if me is None:
            await message.answer(i18n.t("en", "chat.not_registered"))
            return
        lang = me.language_code
        if not handle:
            await message.answer(i18n.t(lang, "friends.usage_addfriend"))
            return

        try:
            friendship = await send_request(
                session, requester=me, addressee_username=handle
            )
        except FriendError as exc:
            await message.answer(i18n.t(lang, "friends.error", reason=str(exc)))
            return

        addressee = await session.get(User, friendship.addressee_id)
        addressee_display = (
            addressee.display_name if addressee else str(friendship.addressee_id)
        )
        addressee_lang = addressee.language_code if addressee else "en"
        addressee_display_name = addressee_display

    # Notify the requester.
    await message.answer(
        i18n.t(lang, "friends.request_sent", name=addressee_display_name)
    )

    # DM the target with accept/decline buttons — if they blocked the bot,
    # they'll only see the pending request the next time they open the app.
    try:
        await message.bot.send_message(
            chat_id=friendship.addressee_id,
            text=i18n.t(
                addressee_lang,
                "friends.incoming_request",
                name=me.display_name,
                username=me.username or "?",
            ),
            reply_markup=_accept_decline_kb(addressee_lang, i18n, friendship.id),
        )
    except (TelegramForbiddenError, TelegramBadRequest) as exc:
        log.info("addfriend: couldn't DM %s (%s)", friendship.addressee_id, exc)


@router.message(Command("friends"))
async def cmd_friends(message: Message) -> None:
    if message.from_user is None:
        return
    i18n = get_i18n()
    async with session_scope() as session:
        me = await session.get(User, message.from_user.id)
        if me is None:
            return
        lang = me.language_code

        friends = await list_friends(session, me.telegram_id)
        incoming = await list_pending_incoming(session, me.telegram_id)
        outgoing = await list_pending_outgoing(session, me.telegram_id)

        friend_names: list[str] = []
        for f in friends:
            other = await session.get(User, counterpart_id(f, me.telegram_id))
            if other:
                friend_names.append(other.display_name)

        incoming_lines: list[str] = []
        for f in incoming:
            requester = await session.get(User, f.requester_id)
            if requester:
                incoming_lines.append(
                    f"• {requester.display_name} (@{requester.username or '?'})"
                )

        outgoing_lines: list[str] = []
        for f in outgoing:
            addressee = await session.get(User, f.addressee_id)
            if addressee:
                outgoing_lines.append(
                    f"• {addressee.display_name} (@{addressee.username or '?'})"
                )

    parts = [
        i18n.t(lang, "friends.list_header", count=len(friends)),
    ]
    if friend_names:
        parts.append("\n".join(f"• {n}" for n in friend_names))
    if incoming_lines:
        parts.append("")
        parts.append(i18n.t(lang, "friends.list_incoming_header"))
        parts.extend(incoming_lines)
    if outgoing_lines:
        parts.append("")
        parts.append(i18n.t(lang, "friends.list_outgoing_header"))
        parts.extend(outgoing_lines)
    if not friend_names and not incoming_lines and not outgoing_lines:
        parts.append(i18n.t(lang, "friends.list_empty"))

    await message.answer("\n".join(parts))


@router.callback_query(F.data.startswith("friend:"))
async def cb_friend(cb: CallbackQuery) -> None:
    if cb.from_user is None or not cb.data:
        await cb.answer()
        return

    parts = cb.data.split(":", 2)
    if len(parts) != 3:
        await cb.answer()
        return
    _, action, friendship_id = parts

    try:
        fid = uuid.UUID(friendship_id)
    except (ValueError, TypeError):
        await cb.answer()
        return

    i18n = get_i18n()

    async with session_scope() as session:
        me = await session.get(User, cb.from_user.id)
        lang = me.language_code if me else "en"
        friendship = await get_friendship(session, friendship_id=fid)
        if friendship is None or me is None:
            await cb.answer(i18n.t(lang, "friends.gone"), show_alert=True)
            if cb.message:
                try:
                    await cb.message.edit_reply_markup(reply_markup=None)
                except Exception:
                    pass
            return

        try:
            if action == "accept":
                await accept_friend(session, friendship=friendship, accepting_user=me)
                # Award the first-friend badge on either side (idempotent).
                await award_badge(
                    session, user_id=me.telegram_id, badge_id="friend_added"
                )
                await award_badge(
                    session,
                    user_id=friendship.requester_id,
                    badge_id="friend_added",
                )
                answer_key = "friends.answered.accepted"
                followup_key = "friends.followup.accepted"
            elif action == "decline":
                await decline_friend(
                    session, friendship=friendship, declining_user=me
                )
                answer_key = "friends.answered.declined"
                followup_key = "friends.followup.declined"
            else:
                await cb.answer()
                return
            requester = await session.get(User, friendship.requester_id)
        except FriendError as exc:
            await cb.answer(i18n.t(lang, "friends.error", reason=str(exc)), show_alert=True)
            return

    await cb.answer(i18n.t(lang, answer_key))
    if cb.message:
        await cb.message.edit_reply_markup(reply_markup=None)
        await cb.message.answer(
            i18n.t(
                lang,
                followup_key,
                name=(requester.display_name if requester else "?"),
            )
        )

    # Ping the requester too so they know it landed.
    if action == "accept" and requester is not None:
        try:
            await cb.bot.send_message(
                chat_id=requester.telegram_id,
                text=i18n.t(
                    requester.language_code,
                    "friends.requester_accepted",
                    name=me.display_name,
                ),
            )
        except (TelegramForbiddenError, TelegramBadRequest):
            pass
