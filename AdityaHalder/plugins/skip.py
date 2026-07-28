from pyrogram import filters
from .. import bot, call, cdx
from ..modules.helpers import AdminsOnlyWrapper


@bot.on_message(cdx(["skip", "cskip"]) & \~filters.private)
@AdminsOnlyWrapper
async def skip_vc_stream(client, message):
    chat_id = message.chat.id
    queued = call.queue.get(chat_id)
    active = chat_id in getattr(call, "active_chats", [])
    if not queued and not active:
        return await message.reply_text("**❌ Nothing streaming.**")
    try:
        if queued and len(queued) > 1:
            await call.change_stream(chat_id)
            return await message.reply_text("**⏭ Skipped to next.**")
        await call.close_stream(chat_id)
        return await message.reply_text("**⏹ Stopped (no more songs).**")
    except Exception:
        return await message.reply_text("**❌ Failed to skip.**")
