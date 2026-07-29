from .. import bot, cdx, rgx, console
from ..modules.database import add_served_user
from ..modules.formatters import smallcaps

from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

try:
    from pyrogram.enums import ButtonStyle

    _PRIMARY = ButtonStyle.PRIMARY
    _SUCCESS = ButtonStyle.SUCCESS
    _DANGER = ButtonStyle.DANGER
except Exception:
    _PRIMARY = "primary"
    _SUCCESS = "success"
    _DANGER = "danger"


def _btn(text: str, style=None, **kwargs) -> InlineKeyboardButton:
    if style is not None:
        try:
            return InlineKeyboardButton(text, style=style, **kwargs)
        except TypeError:
            pass
        try:
            return InlineKeyboardButton(
                text, style=str(getattr(style, "name", style)).lower(), **kwargs
            )
        except TypeError:
            pass
    return InlineKeyboardButton(text, **kwargs)


def start_markup(bot_username: str) -> InlineKeyboardMarkup:
    owner = getattr(console, "OWNER_USERNAME", "") or ""
    support = getattr(console, "SUPPORT_CHAT", "") or ""

    rows = [
        [
            _btn(
                smallcaps("➕ add me to group"),
                _PRIMARY,
                url=f"https://t.me/{bot_username}?startgroup=true",
            ),
        ],
        [
            _btn(smallcaps("📝 help"), _SUCCESS, callback_data="help_menu"),
        ],
    ]

    # Owner + Support / Repo row
    bottom = []
    if owner:
        bottom.append(
            _btn(smallcaps("👑 owner"), _PRIMARY, url=f"https://t.me/{owner}")
        )
    elif getattr(console, "OWNER_ID", 0):
        bottom.append(
            _btn(
                smallcaps("👑 owner"),
                _PRIMARY,
                url=f"tg://user?id={console.OWNER_ID}",
            )
        )

    if support:
        bottom.append(
            _btn(smallcaps("💬 support"), _SUCCESS, url=f"https://t.me/{support}")
        )

    # Last button = REPO (alert)
    bottom.append(
        _btn(smallcaps("📦 repo"), _DANGER, callback_data="repo_alert")
    )

    if bottom:
        rows.append(bottom)

    return InlineKeyboardMarkup(rows)


def help_markup(bot_username: str) -> InlineKeyboardMarkup:
    owner = getattr(console, "OWNER_USERNAME", "") or ""
    support = getattr(console, "SUPPORT_CHAT", "") or ""

    rows = [
        [
            _btn(
                smallcaps("➕ add me to group"),
                _PRIMARY,
                url=f"https://t.me/{bot_username}?startgroup=true",
            ),
        ],
    ]

    link_row = []
    if owner:
        link_row.append(
            _btn(smallcaps("👑 owner"), _PRIMARY, url=f"https://t.me/{owner}")
        )
    elif getattr(console, "OWNER_ID", 0):
        link_row.append(
            _btn(
                smallcaps("👑 owner"),
                _PRIMARY,
                url=f"tg://user?id={console.OWNER_ID}",
            )
        )
    if support:
        link_row.append(
            _btn(smallcaps("💬 support"), _SUCCESS, url=f"https://t.me/{support}")
        )
    link_row.append(
        _btn(smallcaps("📦 repo"), _DANGER, callback_data="repo_alert")
    )
    if link_row:
        rows.append(link_row)

    rows.append(
        [
            _btn(smallcaps("🔙 back"), _DANGER, callback_data="home_menu"),
        ]
    )
    return InlineKeyboardMarkup(rows)


def start_caption(mention: str) -> str:
    body = (
        f"{smallcaps('hey')} {mention}\n\n"
        f"{smallcaps('i am a high quality fast music bot.')}\n"
        f"{smallcaps('add me to your group and enjoy audio / video streaming.')}\n\n"
        f"{smallcaps('use the buttons below for help, owner and support.')}"
    )
    return f"<blockquote expandable>{body}</blockquote>"


def help_caption() -> str:
    body = (
        f"{smallcaps('music bot commands')}\n\n"
        f"{smallcaps('/play')} – {smallcaps('play audio song')}\n"
        f"{smallcaps('/vplay')} – {smallcaps('play video song')}\n"
        f"{smallcaps('/pause')} – {smallcaps('pause current song')}\n"
        f"{smallcaps('/resume')} – {smallcaps('resume paused song')}\n"
        f"{smallcaps('/skip')} – {smallcaps('skip to next track')}\n"
        f"{smallcaps('/end')} – {smallcaps('stop and clear queue')}\n"
        f"{smallcaps('/stats')} – {smallcaps('system statistics')}\n\n"
        f"{smallcaps('tip: use /play with song name or link.')}"
    )
    return f"<blockquote expandable>{body}</blockquote>"


@bot.on_message(cdx(["start", "help"]))
async def start_message_private(client, message):
    try:
        await add_served_user(message.from_user.id)
    except Exception:
        pass

    mention = message.from_user.mention if message.from_user else "User"
    photo = console.START_IMAGE_URL
    caption = start_caption(mention)
    buttons = start_markup(client.me.username)

    try:
        await message.reply_photo(
            photo=photo,
            caption=caption,
            reply_markup=buttons,
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        await message.reply_text(
            caption,
            reply_markup=buttons,
            parse_mode=ParseMode.HTML,
        )

    try:
        full_name = message.from_user.first_name + " " + (
            message.from_user.last_name or ""
        )
        username = (
            f"@{message.from_user.username}" if message.from_user.username else "N/A"
        )
        user_id = message.from_user.id
        log_message = (
            f"🚀 **{mention} Just Started the Bot!**\n\n"
            f"🧑 **Full Name:** {full_name}\n"
            f"🔗 **Username:** {username}\n"
            f"🆔 **Telegram ID:** `{user_id}`"
        )
        await client.send_message(
            console.LOG_GROUP_ID, text=log_message, disable_web_page_preview=True
        )
    except Exception:
        pass


@bot.on_callback_query(rgx("repo_alert"))
async def repo_alert_cb(client, query):
    await query.answer(smallcaps("repo private hai") + " 🔒", show_alert=True)


@bot.on_callback_query(rgx("help_menu"))
async def help_menu_cb(client, query):
    try:
        await query.message.edit_text(
            help_caption(),
            reply_markup=help_markup(client.me.username),
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        try:
            await query.message.edit_caption(
                caption=help_caption(),
                reply_markup=help_markup(client.me.username),
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass
    await query.answer()


@bot.on_callback_query(rgx("home_menu"))
async def home_menu_cb(client, query):
    mention = query.from_user.mention if query.from_user else "User"
    caption = start_caption(mention)
    buttons = start_markup(client.me.username)
    try:
        await query.message.edit_text(
            caption, reply_markup=buttons, parse_mode=ParseMode.HTML
        )
    except Exception:
        try:
            await query.message.edit_caption(
                caption=caption, reply_markup=buttons, parse_mode=ParseMode.HTML
            )
        except Exception:
            pass
    await query.answer()
