from pyrogram import filters

from .. import bot, call, cdx
from ..modules.helpers import AdminsOnlyWrapper


@bot.on_message(cdx(["end", "stop"]) & \~filters.private))
@AdminsOnlyWrapper
async def stop_vc_stream(client, message):
    try:
        await message.delete()
    except Exception:
        pass
    chat_id = message.chat.id
    playing = call.queue.get(chat_id) or (chat_id in getattr(call, "active_chats", []))
    if not playing:
        return await message.reply_text("**Nothing Streaming.**")
    try:
        await call.close_stream(chat_id)
        return await message.reply_text("**Streaming Stopped.**")
    except Exception:
        return await message.reply_text("**Failed to stop.**")
