# ---------------------------------------------------------------
# AdityaHalder — moderation.py
# Admin cmds: mute, unmute, ban, unban, kick (with reason)
# ---------------------------------------------------------------

from pyrogram import filters, enums
from pyrogram.enums import ParseMode
from pyrogram.errors import ChatAdminRequired, UserAdminInvalid, RPCError
from pyrogram.types import Message, ChatPermissions

from .. import bot, cdx, console
from .maintenance import block_if_maintenance, is_sudo


async def _is_admin(client, chat_id, user_id) -> bool:
    if is_sudo(user_id):
        return True
    try:
        m = await client.get_chat_member(chat_id, user_id)
        return m.status in (
            enums.ChatMemberStatus.OWNER,
            enums.ChatMemberStatus.ADMINISTRATOR,
        )
    except Exception:
        return False


async def _get_target_and_reason(client, msg: Message):
    target = None
    reason = None

    if msg.reply_to_message and msg.reply_to_message.from_user:
        target = msg.reply_to_message.from_user
        parts = (msg.text or "").split(None, 1)
        reason = parts[1].strip() if len(parts) > 1 else None
        return target, reason

    if msg.command and len(msg.command) > 1:
        try:
            target = await client.get_users(msg.command[1])
            parts = (msg.text or "").split(None, 2)
            reason = parts[2].strip() if len(parts) > 2 else None
            return target, reason
        except Exception:
            return None, None

    return None, None


def _tag(user):
    name = (user.first_name or "User").replace("<", "").replace(">", "")
    return f'<a href="tg://user?id={user.id}">{name}</a>'


def _reason_line(reason):
    if not reason:
        return ""
    safe = reason.replace("<", "").replace(">", "")
    return f"\n📋 <b>ʀᴇᴀsᴏɴ:</b> {safe}"


async def _reply(client, msg: Message, text: str):
    """Always send to chat — works even if original msg was deleted."""
    try:
        await client.send_message(
            msg.chat.id,
            text,
            parse_mode=ParseMode.HTML,
            reply_to_message_id=(
                msg.reply_to_message.id if msg.reply_to_message else None
            ),
        )
    except Exception:
        try:
            await client.send_message(msg.chat.id, text, parse_mode=ParseMode.HTML)
        except Exception as e:
            print(f"[moderation reply error] {e}", flush=True)


def _mute_permissions() -> ChatPermissions:
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


def _unmute_permissions() -> ChatPermissions:
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


# ── MUTE ─────────────────────────────────────────────────────

@bot.on_message(cdx("mute") & filters.group & filters.incoming)
async def mute_user(client, msg: Message):
    if await block_if_maintenance(msg):
        return

    if not msg.from_user:
        return

    if not await _is_admin(client, msg.chat.id, msg.from_user.id):
        return await _reply(client, msg, "❌ <b>ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴍᴜᴛᴇ!</b>")

    target, reason = await _get_target_and_reason(client, msg)
    if not target:
        return await _reply(
            client,
            msg,
            "❌ <b>ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴜsᴇʀɴᴀᴍᴇ/ɪᴅ!</b>\n"
            "<code>/mute @user reason</code>",
        )

    if target.id == msg.from_user.id:
        return await _reply(client, msg, "❌ <b>ʏᴏᴜ ᴄᴀɴɴᴏᴛ ᴍᴜᴛᴇ ʏᴏᴜʀsᴇʟꜰ!</b>")

    if target.id == (client.me.id if client.me else 0):
        return await _reply(client, msg, "❌ <b>ᴄᴀɴɴᴏᴛ ᴍᴜᴛᴇ ᴛʜᴇ ʙᴏᴛ!</b>")

    try:
        await client.restrict_chat_member(
            msg.chat.id, target.id, _mute_permissions()
        )
        await _reply(
            client,
            msg,
            f"🔇 <b>{_tag(target)} ʜᴀs ʙᴇᴇɴ ᴍᴜᴛᴇᴅ!</b>\n"
            f"👮 <b>ʙʏ:</b> {_tag(msg.from_user)}"
            f"{_reason_line(reason)}",
        )
    except ChatAdminRequired:
        await _reply(client, msg, "❌ <b>ʙᴏᴛ ᴍᴜsᴛ ʙᴇ ᴀᴅᴍɪɴ ᴡɪᴛʜ ʀᴇsᴛʀɪᴄᴛ ʀɪɢʜᴛs!</b>")
    except UserAdminInvalid:
        await _reply(client, msg, "❌ <b>ᴄᴀɴɴᴏᴛ ᴍᴜᴛᴇ ᴀɴ ᴀᴅᴍɪɴ!</b>")
    except RPCError as e:
        await _reply(client, msg, f"❌ <b>ᴇʀʀᴏʀ:</b> <code>{e}</code>")
    except Exception as e:
        await _reply(client, msg, f"❌ <b>ᴇʀʀᴏʀ:</b> <code>{type(e).__name__}: {e}</code>")


# ── UNMUTE ───────────────────────────────────────────────────

@bot.on_message(cdx("unmute") & filters.group & filters.incoming)
async def unmute_user(client, msg: Message):
    if await block_if_maintenance(msg):
        return

    if not msg.from_user:
        return

    if not await _is_admin(client, msg.chat.id, msg.from_user.id):
        return await _reply(client, msg, "❌ <b>ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴜɴᴍᴜᴛᴇ!</b>")

    target, reason = await _get_target_and_reason(client, msg)
    if not target:
        return await _reply(
            client,
            msg,
            "❌ <b>ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴜsᴇʀɴᴀᴍᴇ/ɪᴅ!</b>\n"
            "<code>/unmute @user</code>",
        )

    try:
        await client.restrict_chat_member(
            msg.chat.id, target.id, _unmute_permissions()
        )
        await _reply(
            client,
            msg,
            f"🔊 <b>{_tag(target)} ʜᴀs ʙᴇᴇɴ ᴜɴᴍᴜᴛᴇᴅ!</b>\n"
            f"👮 <b>ʙʏ:</b> {_tag(msg.from_user)}"
            f"{_reason_line(reason)}",
        )
    except ChatAdminRequired:
        await _reply(client, msg, "❌ <b>ʙᴏᴛ ᴍᴜsᴛ ʙᴇ ᴀᴅᴍɪɴ!</b>")
    except Exception as e:
        await _reply(client, msg, f"❌ <b>ᴇʀʀᴏʀ:</b> <code>{type(e).__name__}: {e}</code>")


# ── BAN ──────────────────────────────────────────────────────

@bot.on_message(cdx("ban") & filters.group & filters.incoming)
async def ban_user(client, msg: Message):
    if await block_if_maintenance(msg):
        return

    if not msg.from_user:
        return

    if not await _is_admin(client, msg.chat.id, msg.from_user.id):
        return await _reply(client, msg, "❌ <b>ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ʙᴀɴ!</b>")

    target, reason = await _get_target_and_reason(client, msg)
    if not target:
        return await _reply(
            client,
            msg,
            "❌ <b>ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴜsᴇʀɴᴀᴍᴇ/ɪᴅ!</b>\n"
            "<code>/ban @user reason</code>",
        )

    if target.id == msg.from_user.id:
        return await _reply(client, msg, "❌ <b>ʏᴏᴜ ᴄᴀɴɴᴏᴛ ʙᴀɴ ʏᴏᴜʀsᴇʟꜰ!</b>")

    try:
        await client.ban_chat_member(msg.chat.id, target.id)
        await _reply(
            client,
            msg,
            f"🚫 <b>{_tag(target)} ʜᴀs ʙᴇᴇɴ ʙᴀɴɴᴇᴅ!</b>\n"
            f"👮 <b>ʙʏ:</b> {_tag(msg.from_user)}"
            f"{_reason_line(reason)}",
        )
    except ChatAdminRequired:
        await _reply(client, msg, "❌ <b>ʙᴏᴛ ᴍᴜsᴛ ʙᴇ ᴀᴅᴍɪɴ ᴡɪᴛʜ ʙᴀɴ ʀɪɢʜᴛs!</b>")
    except UserAdminInvalid:
        await _reply(client, msg, "❌ <b>ᴄᴀɴɴᴏᴛ ʙᴀɴ ᴀɴ ᴀᴅᴍɪɴ!</b>")
    except Exception as e:
        await _reply(client, msg, f"❌ <b>ᴇʀʀᴏʀ:</b> <code>{type(e).__name__}: {e}</code>")


# ── UNBAN ────────────────────────────────────────────────────

@bot.on_message(cdx("unban") & filters.group & filters.incoming)
async def unban_user(client, msg: Message):
    if await block_if_maintenance(msg):
        return

    if not msg.from_user:
        return

    if not await _is_admin(client, msg.chat.id, msg.from_user.id):
        return await _reply(client, msg, "❌ <b>ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴜɴʙᴀɴ!</b>")

    target, reason = await _get_target_and_reason(client, msg)
    if not target:
        return await _reply(
            client,
            msg,
            "❌ <b>ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴜsᴇʀɴᴀᴍᴇ/ɪᴅ!</b>\n"
            "<code>/unban @user</code>",
        )

    try:
        await client.unban_chat_member(msg.chat.id, target.id)
        await _reply(
            client,
            msg,
            f"✅ <b>{_tag(target)} ʜᴀs ʙᴇᴇɴ ᴜɴʙᴀɴɴᴇᴅ!</b>\n"
            f"👮 <b>ʙʏ:</b> {_tag(msg.from_user)}"
            f"{_reason_line(reason)}",
        )
    except ChatAdminRequired:
        await _reply(client, msg, "❌ <b>ʙᴏᴛ ᴍᴜsᴛ ʙᴇ ᴀᴅᴍɪɴ!</b>")
    except Exception as e:
        await _reply(client, msg, f"❌ <b>ᴇʀʀᴏʀ:</b> <code>{type(e).__name__}: {e}</code>")


# ── KICK ─────────────────────────────────────────────────────

@bot.on_message(cdx("kick") & filters.group & filters.incoming)
async def kick_user(client, msg: Message):
    if await block_if_maintenance(msg):
        return

    if not msg.from_user:
        return

    if not await _is_admin(client, msg.chat.id, msg.from_user.id):
        return await _reply(client, msg, "❌ <b>ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴋɪᴄᴋ!</b>")

    target, reason = await _get_target_and_reason(client, msg)
    if not target:
        return await _reply(
            client,
            msg,
            "❌ <b>ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴜsᴇʀɴᴀᴍᴇ/ɪᴅ!</b>\n"
            "<code>/kick @user reason</code>",
        )

    if target.id == msg.from_user.id:
        return await _reply(client, msg, "❌ <b>ʏᴏᴜ ᴄᴀɴɴᴏᴛ ᴋɪᴄᴋ ʏᴏᴜʀsᴇʟꜰ!</b>")

    try:
        await client.ban_chat_member(msg.chat.id, target.id)
        await client.unban_chat_member(msg.chat.id, target.id)
        await _reply(
            client,
            msg,
            f"👟 <b>{_tag(target)} ʜᴀs ʙᴇᴇɴ ᴋɪᴄᴋᴇᴅ!</b>\n"
            f"👮 <b>ʙʏ:</b> {_tag(msg.from_user)}"
            f"{_reason_line(reason)}",
        )
    except ChatAdminRequired:
        await _reply(client, msg, "❌ <b>ʙᴏᴛ ᴍᴜsᴛ ʙᴇ ᴀᴅᴍɪɴ ᴡɪᴛʜ ʙᴀɴ ʀɪɢʜᴛs!</b>")
    except UserAdminInvalid:
        await _reply(client, msg, "❌ <b>ᴄᴀɴɴᴏᴛ ᴋɪᴄᴋ ᴀɴ ᴀᴅᴍɪɴ!</b>")
    except Exception as e:
        await _reply(client, msg, f"❌ <b>ᴇʀʀᴏʀ:</b> <code>{type(e).__name__}: {e}</code>")
