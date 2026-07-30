from .. import bot, cdx, rgx, console
from ..modules.database import add_served_user
from ..modules.formatters import smallcaps
from .maintenance import block_if_maintenance, block_cb_if_maintenance

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

ACTION_COMMANDS = [
    ("mute", "/mute"),
    ("unmute", "/unmute"),
    ("ban", "/ban"),
    ("unban", "/unban"),
    ("kick", "/kick"),
]

CHATBOT_COMMANDS = [
    ("chaton", "/chaton"),
    ("chatoff", "/chatoff"),
]

ABUSE_COMMANDS = [
    ("noabuse", "/noabuse"),
]

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
    "mute": (
        f"{smallcaps('command')}: /mute\n\n"
        f"{smallcaps('use')}:\n"
        f"• {smallcaps('reply to user')}: /mute {smallcaps('reason')}\n"
        f"• /mute @user {smallcaps('reason')}\n\n"
        f"{smallcaps('mutes a user in the group. (admin only)')}"
    ),
    "unmute": (
        f"{smallcaps('command')}: /unmute\n\n"
        f"{smallcaps('use')}:\n"
        f"• {smallcaps('reply to user')}: /unmute\n"
        f"• /unmute @user\n\n"
        f"{smallcaps('unmutes a user in the group. (admin only)')}"
    ),
    "ban": (
        f"{smallcaps('command')}: /ban\n\n"
        f"{smallcaps('use')}:\n"
        f"• {smallcaps('reply to user')}: /ban {smallcaps('reason')}\n"
        f"• /ban @user {smallcaps('reason')}\n\n"
        f"{smallcaps('bans a user from the group. (admin only)')}"
    ),
    "unban": (
        f"{smallcaps('command')}: /unban\n\n"
        f"{smallcaps('use')}:\n"
        f"• {smallcaps('reply to user')}: /unban\n"
        f"• /unban @user\n\n"
        f"{smallcaps('unbans a user in the group. (admin only)')}"
    ),
    "kick": (
        f"{smallcaps('command')}: /kick\n\n"
        f"{smallcaps('use')}:\n"
        f"• {smallcaps('reply to user')}: /kick {smallcaps('reason')}\n"
        f"• /kick @user {smallcaps('reason')}\n\n"
        f"{smallcaps('kicks a user from the group. (admin only)')}"
    ),
    "chaton": (
        f"{smallcaps('command')}: /chaton\n\n"
        f"{smallcaps('use')}: /chaton\n\n"
        f"{smallcaps('enables chatbot in this chat.')}\n"
        f"{smallcaps('group: admin only. private: anyone.')}\n"
        f"{smallcaps('then mention bot or say its name to chat.')}"
    ),
    "chatoff": (
        f"{smallcaps('command')}: /chatoff\n\n"
        f"{smallcaps('use')}: /chatoff\n\n"
        f"{smallcaps('disables chatbot in this chat.')}\n"
        f"{smallcaps('group: admin only.')}"
    ),
    "noabuse": (
        f"{smallcaps('command')}: /noabuse\n\n"
        f"{smallcaps('use')}:\n"
        f"• /noabuse on\n"
        f"• /noabuse off\n\n"
        f"{smallcaps('auto deletes abusive messages in group.')}\n"
        f"{smallcaps('admin only. bot needs delete messages right.')}"
    ),
}


def start_markup(bot_username: str) -> InlineKeyboardMarkup:
    owner = getattr(console, "OWNER_USERNAME", "") or ""
    support = getattr(console, "SUPPORT_CHAT", "") or ""
    channel = getattr(console, "SUPPORT_CHANNEL", "") or ""

    if owner:
        owner_btn = _btn(smallcaps("owner"), _PRIMARY, url=f"https://t.me/{owner}")
    elif getattr(console, "OWNER_ID", 0):
        owner_btn = _btn(
            smallcaps("owner"),
            _PRIMARY,
            url=f"tg://user?id={console.OWNER_ID}",
        )
    else:
        owner_btn = _btn(smallcaps("owner"), _PRIMARY, callback_data="about_menu")

    if support:
        support_btn = _btn(
            smallcaps("support"), _SUCCESS, url=f"https://t.me/{support}"
        )
    else:
        support_btn = _btn(
            smallcaps("support"), _SUCCESS, callback_data="support_alert"
        )

    if channel:
        update_btn = _btn(
            smallcaps("update"), _PRIMARY, url=f"https://t.me/{channel}"
        )
    else:
        update_btn = _btn(
            smallcaps("update"), _PRIMARY, callback_data="update_alert"
        )

    return InlineKeyboardMarkup(
        [
            [
                _btn(
                    smallcaps("➕ add me in your group ➕"),
                    _PRIMARY,
                    url=f"https://t.me/{bot_username}?startgroup=true",
                ),
            ],
            [
                owner_btn,
                _btn(smallcaps("about"), _SUCCESS, callback_data="about_menu"),
            ],
            [
                support_btn,
                update_btn,
            ],
            [
                _btn(
                    smallcaps("help and commands"),
                    _PRIMARY,
                    callback_data="help_menu",
                ),
            ],
            [
                _btn(smallcaps("source"), _DANGER, callback_data="repo_alert"),
            ],
        ]
    )


def help_menu_markup() -> InlineKeyboardMarkup:
    rows = []
    row = []
    styles = [_PRIMARY, _SUCCESS, _DANGER]
    for i, (key, _label) in enumerate(HELP_COMMANDS):
        style = styles[i % 3]
        row.append(_btn(smallcaps(key), style, callback_data=f"cmdhelp|{key}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    rows.append(
        [
            _btn(smallcaps("action"), _DANGER, callback_data="action_menu"),
            _btn(smallcaps("chatbot"), _SUCCESS, callback_data="chatbot_menu"),
        ]
    )
    rows.append(
        [
            _btn(smallcaps("abuse"), _DANGER, callback_data="abuse_menu"),
        ]
    )
    rows.append(
        [_btn(smallcaps("🔙 back"), _DANGER, callback_data="home_menu")]
    )
    return InlineKeyboardMarkup(rows)


def action_menu_markup() -> InlineKeyboardMarkup:
    rows = []
    row = []
    styles = [_PRIMARY, _SUCCESS, _DANGER]
    for i, (key, _label) in enumerate(ACTION_COMMANDS):
        style = styles[i % 3]
        row.append(_btn(smallcaps(key), style, callback_data=f"cmdhelp|{key}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append(
        [
            _btn(smallcaps("📋 commands"), _SUCCESS, callback_data="help_menu"),
            _btn(smallcaps("🔙 start"), _DANGER, callback_data="home_menu"),
        ]
    )
    return InlineKeyboardMarkup(rows)


def chatbot_menu_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                _btn(smallcaps("chaton"), _SUCCESS, callback_data="cmdhelp|chaton"),
                _btn(smallcaps("chatoff"), _DANGER, callback_data="cmdhelp|chatoff"),
            ],
            [
                _btn(smallcaps("📋 commands"), _SUCCESS, callback_data="help_menu"),
                _btn(smallcaps("🔙 start"), _DANGER, callback_data="home_menu"),
            ],
        ]
    )


def abuse_menu_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                _btn(smallcaps("noabuse"), _DANGER, callback_data="cmdhelp|noabuse"),
            ],
            [
                _btn(smallcaps("📋 commands"), _SUCCESS, callback_data="help_menu"),
                _btn(smallcaps("🔙 start"), _DANGER, callback_data="home_menu"),
            ],
        ]
    )


def cmd_help_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                _btn(smallcaps("📋 commands"), _SUCCESS, callback_data="help_menu"),
                _btn(smallcaps("🔙 start"), _DANGER, callback_data="home_menu"),
            ],
        ]
    )


def about_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [_btn(smallcaps("🔙 back"), _DANGER, callback_data="home_menu")],
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
        f"{smallcaps('tap any command button below to see how to use it.')}\n"
        f"{smallcaps('action = mute ban kick etc.')}\n"
        f"{smallcaps('chatbot = chaton chatoff')}\n"
        f"{smallcaps('abuse = noabuse filter')}"
    )
    return f"<blockquote expandable>{body}</blockquote>"


def action_list_caption() -> str:
    body = (
        f"{smallcaps('action commands')}\n\n"
        f"{smallcaps('moderation tools for group admins.')}\n"
        f"{smallcaps('tap a button to see usage.')}"
    )
    return f"<blockquote expandable>{body}</blockquote>"


def chatbot_list_caption() -> str:
    body = (
        f"{smallcaps('chatbot commands')}\n\n"
        f"{smallcaps('enable or disable ai chat in this chat.')}\n"
        f"{smallcaps('tap a button to see usage.')}"
    )
    return f"<blockquote expandable>{body}</blockquote>"


def abuse_list_caption() -> str:
    body = (
        f"{smallcaps('abuse filter')}\n\n"
        f"{smallcaps('auto delete bad words in group.')}\n"
        f"{smallcaps('tap noabuse to see usage.')}"
    )
    return f"<blockquote expandable>{body}</blockquote>"


def cmd_usage_caption(key: str) -> str:
    text = CMD_USAGE.get(key, smallcaps("unknown command"))
    return f"<blockquote expandable>{text}</blockquote>"


def about_caption() -> str:
    body = (
        f"{smallcaps('about')}\n\n"
        f"{smallcaps('high quality telegram music bot.')}\n"
        f"{smallcaps('supports audio and video streaming.')}\n"
        f"{smallcaps('powered by pytgcalls + kurigram.')}\n\n"
        f"{smallcaps('add me in your group and start playing.')}"
    )
    return f"<blockquote expandable>{body}</blockquote>"


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
    if await block_if_maintenance(message):
        return

    try:
        await add_served_user(message.from_user.id)
    except Exception:
        pass

    mention = message.from_user.mention if message.from_user else "User"
    photo = console.START_IMAGE_URL
    caption = start_caption(mention)
    buttons = start_markup(client.me.username)

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
    if await block_cb_if_maintenance(query):
        return
    await query.answer(smallcaps("repo private hai") + " 🔒", show_alert=True)


@bot.on_callback_query(rgx("support_alert"))
async def support_alert_cb(client, query):
    if await block_cb_if_maintenance(query):
        return
    await query.answer(
        smallcaps("support chat set nahi hai config me"), show_alert=True
    )


@bot.on_callback_query(rgx("update_alert"))
async def update_alert_cb(client, query):
    if await block_cb_if_maintenance(query):
        return
    await query.answer(
        smallcaps("update channel set nahi hai config me"), show_alert=True
    )


@bot.on_callback_query(rgx("about_menu"))
async def about_menu_cb(client, query):
    if await block_cb_if_maintenance(query):
        return
    await _edit_menu(query, about_caption(), about_markup())
    await query.answer()


@bot.on_callback_query(rgx("help_menu"))
async def help_menu_cb(client, query):
    if await block_cb_if_maintenance(query):
        return
    await _edit_menu(query, help_list_caption(), help_menu_markup())
    await query.answer()


@bot.on_callback_query(rgx("action_menu"))
async def action_menu_cb(client, query):
    if await block_cb_if_maintenance(query):
        return
    await _edit_menu(query, action_list_caption(), action_menu_markup())
    await query.answer()


@bot.on_callback_query(rgx("chatbot_menu"))
async def chatbot_menu_cb(client, query):
    if await block_cb_if_maintenance(query):
        return
    await _edit_menu(query, chatbot_list_caption(), chatbot_menu_markup())
    await query.answer()


@bot.on_callback_query(rgx("abuse_menu"))
async def abuse_menu_cb(client, query):
    if await block_cb_if_maintenance(query):
        return
    await _edit_menu(query, abuse_list_caption(), abuse_menu_markup())
    await query.answer()


@bot.on_callback_query(rgx(r"^cmdhelp\|"))
async def cmd_help_cb(client, query):
    if await block_cb_if_maintenance(query):
        return
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
    if await block_cb_if_maintenance(query):
        return
    mention = query.from_user.mention if query.from_user else "User"
    await _edit_menu(
        query, start_caption(mention), start_markup(client.me.username)
    )
    await query.answer()
