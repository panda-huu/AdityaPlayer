# ---------------------------------------------------------------
# AdityaHalder — welcome.py
# /welcome on|off  |  /setwelcome  |  /resetwelcome
# Custom text + photo/video + inline buttons
# ---------------------------------------------------------------

print("[welcome] loading plugin...", flush=True)

import asyncio
import json
import os
import random
import re
import traceback

from pyrogram import filters
from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import bot, console

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DB_PATH = os.path.join(_BASE_DIR, "welcome_db.json")

DEFAULT_IMAGES = [
    "https://files.catbox.moe/nacfzm.jpg",
    "https://files.catbox.moe/x4lzbx.jpg",
    "https://files.catbox.moe/g6cmb2.jpg",
    "https://files.catbox.moe/3hxb96.jpg",
]

DEFAULT_TEXT = (
    "🌸✨ ──────────────────── ✨🌸\n"
    "🌹 <b>Name</b> ➤ {name}\n"
    "🆔 <b>User ID</b> ➤ <code>{id}</code>\n"
    "🏠 <b>Group</b> ➤ {chat}\n"
    "🌸✨ ──────────────────── ✨🌸"
)

_BTN_RE = re.compile(
    r"\[([^\]]+)\]\(buttonurl:(https?://[^\s\)]+)\)",
    re.IGNORECASE,
)


def _load_db() -> dict:
    try:
        if os.path.exists(_DB_PATH):
            with open(_DB_PATH, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_db(data: dict):
    try:
        with open(_DB_PATH, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[welcome] save error: {e}", flush=True)


def _default_cfg():
    return {
        "enabled": True,
        "text": None,
        "media": None,       # file_id
        "media_type": None,  # photo | video | animation
        "buttons": [],
    }


def _chat_cfg(chat_id: int) -> dict:
    db = _load_db()
    key = str(chat_id)
    if key not in db:
        db[key] = _default_cfg()
        _save_db(db)
    cfg = db[key]
    # migrate old "photo" key
    if cfg.get("photo") and not cfg.get("media"):
        cfg["media"] = cfg["photo"]
        cfg["media_type"] = "photo"
    return cfg


def _set_chat_cfg(chat_id: int, **kwargs):
    db = _load_db()
    key = str(chat_id)
    cfg = db.get(key) or _default_cfg()
    cfg.update(kwargs)
    db[key] = cfg
    _save_db(db)


def is_enabled(chat_id: int) -> bool:
    return bool(_chat_cfg(chat_id).get("enabled", True))


def parse_buttons(text: str):
    if not text:
        return text, []
    buttons = []
    for m in _BTN_RE.finditer(text):
        buttons.append({"text": m.group(1).strip(), "url": m.group(2).strip()})
    clean = _BTN_RE.sub("", text).strip()
    clean = re.sub(r"\n{3,}", "\n\n", clean)
    return clean, buttons


def build_markup(buttons: list):
    if not buttons:
        channel = (getattr(console, "SUPPORT_CHANNEL", "") or "").lstrip("@")
        if channel:
            return InlineKeyboardMarkup(
                [[InlineKeyboardButton("• Updates •", url=f"https://t.me/{channel}")]]
            )
        return None

    rows = []
    row = []
    for b in buttons:
        row.append(InlineKeyboardButton(b["text"], url=b["url"]))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def format_welcome(template: str, user, chat_title: str) -> str:
    name = user.first_name or "User"
    last = user.last_name or ""
    fullname = f"{name} {last}".strip()
    mention = f'<a href="tg://user?id={user.id}">{name}</a>'
    username = f"@{user.username}" if user.username else "N/A"

    text = template or DEFAULT_TEXT
    text = text.replace("{name}", name)
    text = text.replace("{fullname}", fullname)
    text = text.replace("{id}", str(user.id))
    text = text.replace("{mention}", mention)
    text = text.replace("{username}", username)
    text = text.replace("{chat}", chat_title or "Group")
    text = text.replace("{chat_title}", chat_title or "Group")
    return text


async def is_admin(client, chat_id: int, user_id: int) -> bool:
    try:
        if user_id and user_id == getattr(console, "OWNER_ID", 0):
            return True
        if user_id in getattr(console, "sudoers", []):
            return True
    except Exception:
        pass
    try:
        m = await client.get_chat_member(chat_id, user_id)
        return m.status in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR)
    except Exception:
        return False


async def _send(client, chat_id, text):
    try:
        return await client.send_message(chat_id, text, parse_mode=ParseMode.HTML)
    except Exception:
        try:
            return await client.send_message(chat_id, text)
        except Exception as e:
            print(f"[welcome] send error: {e}", flush=True)


async def _delete_later(msg, delay: int):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass


async def _send_welcome(client, chat_id, caption, media, media_type, markup):
    if media and media_type == "video":
        return await client.send_video(
            chat_id,
            video=media,
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=markup,
        )
    if media and media_type == "animation":
        return await client.send_animation(
            chat_id,
            animation=media,
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=markup,
        )
    if media and media_type == "photo":
        return await client.send_photo(
            chat_id,
            photo=media,
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=markup,
        )
    # default random image
    try:
        return await client.send_photo(
            chat_id,
            photo=random.choice(DEFAULT_IMAGES),
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=markup,
        )
    except Exception:
        return await client.send_message(
            chat_id,
            caption,
            parse_mode=ParseMode.HTML,
            reply_markup=markup,
        )


# ── /welcome on|off ───────────────────────────────────────────

@bot.on_message(
    filters.command(["welcome"], ["/", "!", "."])
    & ~filters.private
    & filters.incoming,
    group=0,
)
async def welcome_toggle(client, msg: Message):
    chat_id = msg.chat.id
    try:
        await msg.delete()
    except Exception:
        pass

    if not msg.from_user:
        return

    if not await is_admin(client, chat_id, msg.from_user.id):
        return await _send(client, chat_id, "❌ <b>Only admins can use this!</b>")

    args = msg.command or []
    if len(args) < 2 or args[1].lower() not in ("on", "off"):
        status = "✅ ON" if is_enabled(chat_id) else "❌ OFF"
        return await _send(
            client,
            chat_id,
            f"<b>👋 Welcome Status:</b> {status}\n\n"
            f"➻ /welcome on\n"
            f"➻ /welcome off\n"
            f"➻ /setwelcome — set custom message (text/photo/video)\n"
            f"➻ /resetwelcome — reset to default",
        )

    if args[1].lower() == "on":
        _set_chat_cfg(chat_id, enabled=True)
        await _send(client, chat_id, "✅ <b>Welcome messages ENABLED!</b>")
    else:
        _set_chat_cfg(chat_id, enabled=False)
        await _send(client, chat_id, "❌ <b>Welcome messages DISABLED!</b>")


# ── /setwelcome ───────────────────────────────────────────────

@bot.on_message(
    filters.command(["setwelcome"], ["/", "!", "."])
    & ~filters.private
    & filters.incoming,
    group=0,
)
async def set_welcome(client, msg: Message):
    chat_id = msg.chat.id
    try:
        await msg.delete()
    except Exception:
        pass

    if not msg.from_user:
        return

    if not await is_admin(client, chat_id, msg.from_user.id):
        return await _send(client, chat_id, "❌ <b>Only admins can set welcome!</b>")

    media = None
    media_type = None
    raw_text = None

    if msg.reply_to_message:
        r = msg.reply_to_message
        if r.video:
            media = r.video.file_id
            media_type = "video"
            raw_text = r.caption or ""
        elif r.animation:
            media = r.animation.file_id
            media_type = "animation"
            raw_text = r.caption or ""
        elif r.photo:
            media = r.photo.file_id
            media_type = "photo"
            raw_text = r.caption or ""
        elif r.text:
            raw_text = r.text
        elif r.caption:
            raw_text = r.caption

    if raw_text is None:
        parts = (msg.text or "").split(None, 1)
        if len(parts) > 1:
            raw_text = parts[1]

    if not raw_text and not media:
        return await _send(
            client,
            chat_id,
            "❌ <b>Usage:</b>\n\n"
            "• <code>/setwelcome Welcome {name}</code>\n"
            "• Reply to a <b>photo</b> with <code>/setwelcome</code>\n"
            "• Reply to a <b>video / gif</b> with <code>/setwelcome</code>\n"
            "• Reply to text with <code>/setwelcome</code>\n\n"
            "<b>Placeholders:</b>\n"
            "{name} {fullname} {id} {mention} {username} {chat}\n\n"
            "<b>Buttons:</b>\n"
            "[Click](buttonurl:https://t.me/example)",
        )

    clean, buttons = parse_buttons(raw_text or "")
    _set_chat_cfg(
        chat_id,
        enabled=True,
        text=clean or None,
        media=media,
        media_type=media_type,
        photo=None,  # clear old key
        buttons=buttons,
    )

    media_label = media_type or "None"
    await _send(
        client,
        chat_id,
        "✅ <b>Welcome message set!</b>\n\n"
        f"Media: <code>{media_label}</code>\n"
        f"Buttons: {len(buttons)}\n"
        f"Text preview:\n<code>{(clean or DEFAULT_TEXT)[:200]}</code>",
    )


# ── /resetwelcome ─────────────────────────────────────────────

@bot.on_message(
    filters.command(["resetwelcome"], ["/", "!", "."])
    & ~filters.private
    & filters.incoming,
    group=0,
)
async def reset_welcome(client, msg: Message):
    chat_id = msg.chat.id
    try:
        await msg.delete()
    except Exception:
        pass

    if not msg.from_user:
        return

    if not await is_admin(client, chat_id, msg.from_user.id):
        return await _send(client, chat_id, "❌ <b>Only admins can reset welcome!</b>")

    _set_chat_cfg(
        chat_id,
        text=None,
        media=None,
        media_type=None,
        photo=None,
        buttons=[],
        enabled=True,
    )
    await _send(client, chat_id, "✅ <b>Welcome reset to default!</b>")


# ── New member join ───────────────────────────────────────────

@bot.on_message(filters.new_chat_members & filters.group, group=99)
async def welcome_new_member(client, message: Message):
    chat_id = message.chat.id

    if not is_enabled(chat_id):
        return

    cfg = _chat_cfg(chat_id)
    chat_title = message.chat.title or "this group"

    try:
        me = client.me or await client.get_me()
    except Exception:
        me = None

    for user in message.new_chat_members:
        if me and user.id == me.id:
            continue
        if user.is_bot:
            continue

        template = cfg.get("text") or DEFAULT_TEXT
        caption = format_welcome(template, user, chat_title)
        media = cfg.get("media") or cfg.get("photo")
        media_type = cfg.get("media_type") or ("photo" if media else None)
        buttons = cfg.get("buttons") or []
        markup = build_markup(buttons)

        try:
            wel = await _send_welcome(
                client, chat_id, caption, media, media_type, markup
            )
            asyncio.create_task(_delete_later(wel, 300))
        except Exception:
            print("[welcome] send failed:", flush=True)
            traceback.print_exc()


print("[welcome] plugin loaded OK", flush=True)
