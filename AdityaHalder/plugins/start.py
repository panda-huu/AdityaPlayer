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


# Command list for help menu (shown 3 per row)
HELP_COMMANDS = [
    ("play", "/play"),
    ("vplay", "/vplay"),
    ("pause", "/pause"),
    ("resume", "/resume"),
    ("skip", "/skip"),
    ("end", "/end"),
    ("stats", "/stats"),
    ("active", "/active"),
    ("broadcast", "/broadcast"),
]

# Usage text for each command (smallcaps body)
CMD_USAGE = {
    "play": (
        f"{smallcaps('command')}: /play\n\n"
        f"{smallcaps('use')}:\n"
        f"• /play {smallcaps('song name')}\n"
        f"• /play {smallcaps('youtube link')}\n"
        f"• {smallcaps('reply to audio with')} /play\n\n"
        f"{smallcaps('plays audio in voice chat.')}"
    ),
    "vplay": (
        f"{smallcaps('command')}: /vplay\n\n"
        f"{smallcaps('use')}:\n"
        f"• /vplay {smallcaps('song name')}\n"
        f"• /vplay {smallcaps('youtube link')}\n"
        f"• {smallcaps('reply to video with')} /vplay\n\n"
        f"{smallcaps('plays video in voice chat.')}"
    ),
    "pause": (
        f"{smallcaps('command')}: /pause\n\n"
        f"{smallcaps('use')}: /pause\n\n"
        f"{smallcaps('pauses the current stream.')}"
    ),
    "resume": (
        f"{smallcaps('command')}: /resume\n\n"
        f"{smallcaps('use')}: /resume\n\n"
        f"{smallcaps('resumes the paused stream.')}"
    ),
    "skip": (
        f"{smallcaps('command')}: /skip\n\n"
        f"{smallcaps('use')}: /skip\n\n"
        f"{smallcaps('skips to the next track in queue.')}"
    ),
    "end": (
        f"{smallcaps('command')}: /end\n\n"
        f"{smallcaps('use')}: /end\n\n"
        f"{smallcaps('stops streaming and clears the queue.')}"
    ),
    "stats": (
        f"{smallcaps('command')}: /stats\n\n"
        f"{smallcaps('use')}: /stats\n\n"
        f"{smallcaps('shows system and bot statistics.')}"
    ),
    "active": (
        f"{smallcaps('command')}: /active\n\n"
        f"{smallcaps('use')}: /active\n\n"
        f"{smallcaps('shows active voice chats. (owner only)')}"
    ),
    "broadcast": (
        f"{smallcaps('command')}: /broadcast\n\n"
        f"{smallcaps('use')}: /broadcast {smallcaps('message')}\n\n"
        f"{smallcaps('broadcasts message to served users/chats. (owner only)')}"
    ),
}


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

    bottom.append(
        _btn(smallcaps("📦 repo"), _DANGER, callback_data="repo_alert")
    )

    if bottom:
        rows.append(bottom)

    return InlineKeyboardMarkup(rows)


def help_menu_markup() -> InlineKeyboardMarkup:
    """Command buttons — 3 per row + Back."""
    rows = []
    row = []
    styles = [_PRIMARY, _SUCCESS, _DANGER]
    for i, (key, _label) in enumerate(HELP_COMMANDS):
        style = styles[i % 3]
        row.append(
            _btn(smallcaps(key), style, callback_data=f"cmdhelp|{key}")
        )
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    rows.append(
        [
            _btn(smallcaps("🔙 back"), _DANGER, callback_data="home_menu"),
        ]
    )
    return InlineKeyboardMarkup(rows)


def cmd_help_markup() -> InlineKeyboardMarkup:
    """Back to help list + Back to start."""
    return InlineKeyboardMarkup(
        [
            [
                _btn(smallcaps("📋 commands"), _SUCCESS, callback_data="help_menu"),
                _btn(smallcaps("🔙 start"), _DANGER, callback_data="home_menu"),
            ],
        ]
    )


def start_caption(mention: str) -> str:
    body = (
        f"{smallcaps('hey')} {mention}\n\n"
        f"{smallcaps('i am a high quality fast music bot.')}\n"
        f"{smallcaps('add me to your group and enjoy audio / video streaming.')}\n\n"
        f"{smallcaps('use the buttons below for help, owner and support.')}"
    )
    return f"<blockquote expandable>{body}</blockquote>"


def help_list_caption() -> str:
    body = (
        f"{smallcaps('help menu')}\n\n"
        f"{smallcaps('tap any command button below to see how to use it.')}"
    )
    return f"<blockquote expandable>{body}</blockquote>"


def cmd_usage_caption(key: str) -> str:
    text = CMD_USAGE.get(key, smallcaps("unknown command"))
    return f"<blockquote expandable>{text}</blockquote>"


async def _edit_menu(query, caption: str, markup: InlineKeyboardMarkup):
    try:
        await query.message.edit_text(
            caption, reply_markup=markup, parse_mode=ParseMode.HTML
        )
    except Exception:
        try:
            await query.message.edit_caption(
                caption=caption, reply_markup=markup, parse_mode=ParseMode.HTML
            )
        except Exception:
            pass


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

    # /help directly opens command menu
    if message.command and message.command[0].lower() == "help":
        caption = help_list_caption()
        buttons = help_menu_markup()

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

    if message.command and message.command[0].lower() == "start":
        try:
            full_name = message.from_user.first_name + " " + (
                message.from_user.last_name or ""
            )
            username = (
                f"@{message.from_user.username}"
                if message.from_user.username
                else "N/A"
            )
            user_id = message.from_user.id
            mention = message.from_user.mention
            log_message = (
                f"🚀 **{mention} Just Started the Bot!**\n\n"
                f"🧑 **Full Name:** {full_name}\n"
                f"🔗 **Username:** {username}\n"
                f"🆔 **Telegram ID:** `{user_id}`"
            )
            await client.send_message(
                console.LOG_GROUP_ID,
                text=log_message,
                disable_web_page_preview=True,
            )
        except Exception:
            pass


@bot.on_callback_query(rgx("repo_alert"))
async def repo_alert_cb(client, query):
    await query.answer(smallcaps("repo private hai") + " 🔒", show_alert=True)


@bot.on_callback_query(rgx("help_menu"))
async def help_menu_cb(client, query):
    await _edit_menu(query, help_list_caption(), help_menu_markup())
    await query.answer()


@bot.on_callback_query(rgx(r"^cmdhelp\|"))
async def cmd_help_cb(client, query):
    try:
        key = query.data.split("|", 1)[1].strip().lower()
    except Exception:
        return await query.answer("Invalid.", show_alert=True)

    if key not in CMD_USAGE:
        return await query.answer("Unknown command.", show_alert=True)

    await _edit_menu(query, cmd_usage_caption(key), cmd_help_markup())
    await query.answer()


@bot.on_callback_query(rgx("home_menu"))
async def home_menu_cb(client, query):
    mention = query.from_user.mention if query.from_user else "User"
    await _edit_menu(
        query, start_caption(mention), start_markup(client.me.username)
    )
    await query.answer()
