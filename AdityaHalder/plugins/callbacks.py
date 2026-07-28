import time
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from .. import bot, call, rgx
from ..modules.helpers import AssistantErr


def _fmt(seconds: int) -> str:
    seconds = max(0, int(seconds))
    m, s = divmod(seconds, 60)
    return f"{m}:{s:02d}"


def _parse_duration(dur: str) -> int:
    """'3:45' -> 225 seconds"""
    try:
        parts = [int(x) for x in str(dur).split(":")]
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
    except Exception:
        pass
    return 0


def _progress_bar(elapsed: int, total: int, width: int = 9) -> str:
    if total <= 0:
        return f"{_fmt(elapsed)} {'─' * width}● ∞"
    ratio = min(elapsed / total, 1.0)
    pos = min(round(ratio * width), width)
    bar = "─" * pos + "●" + "─" * (width - pos)
    return f"{_fmt(elapsed)} {bar} {_fmt(total)}"


def _is_playing(chat_id: int) -> bool:
    queued = call.queue.get(chat_id)
    if queued:
        return True
    return chat_id in getattr(call, "active_chats", [])


@bot.on_callback_query(rgx("close"))
async def close_cb(client, query):
    try:
        await query.message.delete()
    except Exception:
        pass


@bot.on_callback_query(rgx(r"^PLAYER "))
async def player_panel_cb(client, query):
    try:
        data = query.data.strip()
        _, action_chat = data.split(None, 1)
        action, chat_id_s = action_chat.split("|")
        chat_id = int(chat_id_s)
        action = action.strip()
    except Exception:
        return await query.answer("Invalid button.", show_alert=True)

    if not _is_playing(chat_id):
        return await query.answer("❌ Nothing playing.", show_alert=True)

    # ── Pause ──
    if action == "Pause":
        try:
            await call.pause_stream(chat_id)
            await call.stream_off(chat_id)
            await query.answer("⏸ Paused", show_alert=True)
        except Exception as e:
            await query.answer(f"Error: {type(e).__name__}", show_alert=True)

    # ── Resume ──
    elif action == "Resume":
        try:
            await call.resume_stream(chat_id)
            await call.stream_on(chat_id)
            await query.answer("▶️ Resumed", show_alert=True)
        except Exception as e:
            await query.answer(f"Error: {type(e).__name__}", show_alert=True)

    # ── Skip ──
    elif action == "Skip":
        try:
            queued = call.queue.get(chat_id) or []
            if len(queued) <= 1:
                await call.close_stream(chat_id)
                await query.answer("⏹ Stopped (queue empty)", show_alert=True)
                try:
                    await query.message.delete()
                except Exception:
                    pass
            else:
                await call.change_stream(chat_id)
                await query.answer("⏭ Skipped", show_alert=True)
        except Exception as e:
            await query.answer(f"Error: {type(e).__name__}", show_alert=True)

    # ── Stop ──
    elif action == "Stop":
        try:
            await call.close_stream(chat_id)
            await query.answer("⏹ Stopped", show_alert=True)
            try:
                await query.message.delete()
            except Exception:
                pass
            await bot.send_message(
                chat_id,
                f"🛑 **Streaming stopped by** {query.from_user.mention}",
            )
        except Exception as e:
            await query.answer(f"Error: {type(e).__name__}", show_alert=True)

    # ── Progress ──
    elif action == "Progress":
        try:
            queued = call.queue.get(chat_id) or []
            if not queued:
                return await query.answer("Nothing playing.", show_alert=True)

            item = queued[0]
            title = str(item.get("title", "Unknown"))[:25]
            total = _parse_duration(item.get("duration", "0:00"))
            start = getattr(call, "start_times", {}).get(chat_id)
            elapsed = int(time.time() - start) if start else 0
            if total:
                elapsed = min(elapsed, total)

            bar = _progress_bar(elapsed, total)
            await query.answer(f"{title}\n{bar}", show_alert=True)

            # Update button text on panel
            try:
                new_markup = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("▷", callback_data=f"PLAYER Resume|{chat_id}"),
                            InlineKeyboardButton("II", callback_data=f"PLAYER Pause|{chat_id}"),
                            InlineKeyboardButton("‣‣I", callback_data=f"PLAYER Skip|{chat_id}"),
                            InlineKeyboardButton("▢", callback_data=f"PLAYER Stop|{chat_id}"),
                        ],
                        [
                            InlineKeyboardButton(bar, callback_data=f"PLAYER Progress|{chat_id}"),
                        ],
                        [
                            InlineKeyboardButton("🗑️ Close", callback_data="close"),
                        ],
                    ]
                )
                await query.message.edit_reply_markup(reply_markup=new_markup)
            except Exception:
                pass
        except Exception as e:
            await query.answer(f"Error: {type(e).__name__}", show_alert=True)

    else:
        await query.answer("Unknown action.", show_alert=True)
