# ---------------------------------------------------------------
# AdityaHalder — moderation.py
# Admin cmds: mute, unmute, ban, unban, kick
# ---------------------------------------------------------------

from pyrogram import filters
from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.types import Message, ChatPermissions

from .. import bot, cdx
from .maintenance import block_if_maintenance, is_sudo


async def _is_admin(client, chat_id: int, user_id: int) -> bool:
    if is_sudo(user_id):
        return True
    try:
        m = await client.get_chat_member(chat_id, user_id)
        return m.status in (
            ChatMemberStatus.OWNER,
            ChatMemberStatus.ADMINISTRATOR,
        )
    except Exception as e:
        print(f"[moderation] admin check failed: {e}", flush=True)
        return False


async def _get_target_and_reason(client, msg: Message):
    target = None
    reason = None

    if msg.reply_to_message and msg.reply_to_message.from_user:
        target = msg.reply_to_message.from_user
        parts = (msg.text or "").split(None, 1)
        reason = parts[1].strip() if len(parts) > 1 else None
        return target, reason

    cmd = msg.command or []
    if len(cmd) > 1:
        try:
            target = await client.get_users(cmd[1])
            parts = (msg.text or "").split(None, 2)
            reason = parts[2].strip() if len(parts) > 2 else None
            return target, reason
        except Exception as e:
            print(f"[moderation] get_users failed: {e}", flush=True)
            return None, None

    return None, None


def _tag(user):
    name = (user.first_name or "User").replace("<", "").replace(">", "")
    return f'<a href="tg://user?id={user.id}">{name}</a>'


def _reason_line(reason):
    if not reason:
        return ""
    safe = str(reason).replace("<", "").replace(">", "")
    return f"\n📋 <b>Reason:</b> {safe}"


async def _send(client, chat_id: int, text: str, reply_id=None):
    try:
        return await client.send_message(
            chat_id,
            text,
            parse_mode=ParseMode.HTML,
            reply_to_message_id=reply_id,
        )
    except Exception:
        try:
            return await client.send_message(
                chat_id, text, parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"[moderation] send failed: {e}", flush=True)
            return None


def _mute_perms():
    try:
        return ChatPermissions(all_perms=False)
    except TypeError:
        pass
    try:
        return ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
            can_send_polls=False,
        )
    except TypeError:
        return ChatPermissions(can_send_messages=False)


def _unmute_perms():
    try:
        return ChatPermissions(all_perms=True)
    except TypeError:
        pass
    try:
        return ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_send_polls=True,
        )
    except TypeError:
        return ChatPermissions(can_send_messages=True)


# Same filter style as working pause/play plugins: ~filters.private
_group = ~filters.private


@bot.on_message(cdx("mute") & _group)
async def mute_user(client, msg: Message):
    print(f"[moderation] /mute received chat={msg.chat.id}", flush=True)

    if await block_if_maintenance(msg):
        return

    if not msg.from_user:
        return

    chat_id = msg.chat.id
    reply_id = msg.reply_to_message.id if msg.reply_to_message else None

    if not await _is_admin(client, chat_id, msg.from_user.id):
        return await _send(
            client, chat_id, "❌ <b>Only admins can mute!</b>", reply_id
        )

    target, reason = await _get_target_and_reason(client, msg)
    if not target:
        return await _send(
            client,
            chat_id,
            "❌ <b>Reply to a user or use:</b>\n<code>/mute @user reason</code>",
            reply_id,
        )

    if target.id == msg.from_user.id:
        return await _send(
            client, chat_id, "❌ <b>You cannot mute yourself!</b>", reply_id
        )

    try:
        await client.restrict_chat_member(chat_id, target.id, _mute_perms())
        await _send(
            client,
            chat_id,
            f"🔇 <b>{_tag(target)} has been muted!</b>\n"
            f"👮 <b>By:</b> {_tag(msg.from_user)}"
            f"{_reason_line(reason)}",
            reply_id,
        )
    except Exception as e:
        err = str(e)
        if "CHAT_ADMIN_REQUIRED" in err or "admin" in err.lower():
            await _send(
                client,
                chat_id,
                "❌ <b>Bot must be admin with Restrict Users permission!</b>",
                reply_id,
            )
        elif "USER_ADMIN" in err.upper():
            await _send(
                client, chat_id, "❌ <b>Cannot mute an admin!</b>", reply_id
            )
        else:
            await _send(
                client,
                chat_id,
                f"❌ <b>Error:</b> <code>{type(e).__name__}: {e}</code>",
                reply_id,
            )


@bot.on_message(cdx("unmute") & _group)
async def unmute_user(client, msg: Message):
    print(f"[moderation] /unmute received chat={msg.chat.id}", flush=True)

    if await block_if_maintenance(msg):
        return

    if not msg.from_user:
        return

    chat_id = msg.chat.id
    reply_id = msg.reply_to_message.id if msg.reply_to_message else None

    if not await _is_admin(client, chat_id, msg.from_user.id):
        return await _send(
            client, chat_id, "❌ <b>Only admins can unmute!</b>", reply_id
        )

    target, reason = await _get_target_and_reason(client, msg)
    if not target:
        return await _send(
            client,
            chat_id,
            "❌ <b>Reply to a user or use:</b>\n<code>/unmute @user</code>",
            reply_id,
        )

    try:
        await client.restrict_chat_member(chat_id, target.id, _unmute_perms())
        await _send(
            client,
            chat_id,
            f"🔊 <b>{_tag(target)} has been unmuted!</b>\n"
            f"👮 <b>By:</b> {_tag(msg.from_user)}"
            f"{_reason_line(reason)}",
            reply_id,
        )
    except Exception as e:
        await _send(
            client,
            chat_id,
            f"❌ <b>Error:</b> <code>{type(e).__name__}: {e}</code>",
            reply_id,
        )


@bot.on_message(cdx("ban") & _group)
async def ban_user(client, msg: Message):
    print(f"[moderation] /ban received chat={msg.chat.id}", flush=True)

    if await block_if_maintenance(msg):
        return

    if not msg.from_user:
        return

    chat_id = msg.chat.id
    reply_id = msg.reply_to_message.id if msg.reply_to_message else None

    if not await _is_admin(client, chat_id, msg.from_user.id):
        return await _send(
            client, chat_id, "❌ <b>Only admins can ban!</b>", reply_id
        )

    target, reason = await _get_target_and_reason(client, msg)
    if not target:
        return await _send(
            client,
            chat_id,
            "❌ <b>Reply to a user or use:</b>\n<code>/ban @user reason</code>",
            reply_id,
        )

    if target.id == msg.from_user.id:
        return await _send(
            client, chat_id, "❌ <b>You cannot ban yourself!</b>", reply_id
        )

    try:
        await client.ban_chat_member(chat_id, target.id)
        await _send(
            client,
            chat_id,
            f"🚫 <b>{_tag(target)} has been banned!</b>\n"
            f"👮 <b>By:</b> {_tag(msg.from_user)}"
            f"{_reason_line(reason)}",
            reply_id,
        )
    except Exception as e:
        err = str(e)
        if "CHAT_ADMIN_REQUIRED" in err or "admin" in err.lower():
            await _send(
                client,
                chat_id,
                "❌ <b>Bot must be admin with Ban Users permission!</b>",
                reply_id,
            )
        elif "USER_ADMIN" in err.upper():
            await _send(
                client, chat_id, "❌ <b>Cannot ban an admin!</b>", reply_id
            )
        else:
            await _send(
                client,
                chat_id,
                f"❌ <b>Error:</b> <code>{type(e).__name__}: {e}</code>",
                reply_id,
            )


@bot.on_message(cdx("unban") & _group)
async def unban_user(client, msg: Message):
    print(f"[moderation] /unban received chat={msg.chat.id}", flush=True)

    if await block_if_maintenance(msg):
        return

    if not msg.from_user:
        return

    chat_id = msg.chat.id
    reply_id = msg.reply_to_message.id if msg.reply_to_message else None

    if not await _is_admin(client, chat_id, msg.from_user.id):
        return await _send(
            client, chat_id, "❌ <b>Only admins can unban!</b>", reply_id
        )

    target, reason = await _get_target_and_reason(client, msg)
    if not target:
        return await _send(
            client,
            chat_id,
            "❌ <b>Reply to a user or use:</b>\n<code>/unban @user</code>",
            reply_id,
        )

    try:
        await client.unban_chat_member(chat_id, target.id)
        await _send(
            client,
            chat_id,
            f"✅ <b>{_tag(target)} has been unbanned!</b>\n"
            f"👮 <b>By:</b> {_tag(msg.from_user)}"
            f"{_reason_line(reason)}",
            reply_id,
        )
    except Exception as e:
        await _send(
            client,
            chat_id,
            f"❌ <b>Error:</b> <code>{type(e).__name__}: {e}</code>",
            reply_id,
        )


@bot.on_message(cdx("kick") & _group)
async def kick_user(client, msg: Message):
    print(f"[moderation] /kick received chat={msg.chat.id}", flush=True)

    if await block_if_maintenance(msg):
        return

    if not msg.from_user:
        return

    chat_id = msg.chat.id
    reply_id = msg.reply_to_message.id if msg.reply_to_message else None

    if not await _is_admin(client, chat_id, msg.from_user.id):
        return await _send(
            client, chat_id, "❌ <b>Only admins can kick!</b>", reply_id
        )

    target, reason = await _get_target_and_reason(client, msg)
    if not target:
        return await _send(
            client,
            chat_id,
            "❌ <b>Reply to a user or use:</b>\n<code>/kick @user reason</code>",
            reply_id,
        )

    if target.id == msg.from_user.id:
        return await _send(
            client, chat_id, "❌ <b>You cannot kick yourself!</b>", reply_id
        )

    try:
        await client.ban_chat_member(chat_id, target.id)
        await client.unban_chat_member(chat_id, target.id)
        await _send(
            client,
            chat_id,
            f"👟 <b>{_tag(target)} has been kicked!</b>\n"
            f"👮 <b>By:</b> {_tag(msg.from_user)}"
            f"{_reason_line(reason)}",
            reply_id,
        )
    except Exception as e:
        err = str(e)
        if "CHAT_ADMIN_REQUIRED" in err or "admin" in err.lower():
            await _send(
                client,
                chat_id,
                "❌ <b>Bot must be admin with Ban Users permission!</b>",
                reply_id,
            )
        elif "USER_ADMIN" in err.upper():
            await _send(
                client, chat_id, "❌ <b>Cannot kick an admin!</b>", reply_id
            )
        else:
            await _send(
                client,
                chat_id,
                f"❌ <b>Error:</b> <code>{type(e).__name__}: {e}</code>",
                reply_id,
            )
