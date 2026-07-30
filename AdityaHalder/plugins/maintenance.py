from pyrogram import filters, StopPropagation, ContinuePropagation
from pyrogram.types import Message

from .. import bot, cdx, console

# ── Maintenance state ─────────────────────────────────────────────────────
MAINTENANCE_MODE: bool = False
MAINTENANCE_MSG: str = (
    "🛠 **Bot is currently under maintenance.**\n"
    "Please try again later."
)

PREFIXES = ("/", "!", ".")


def _is_sudo(user_id: int) -> bool:
    if not user_id:
        return False
    if user_id == getattr(console, "OWNER_ID", 0):
        return True
    try:
        return user_id in console.sudoers
    except Exception:
        return False


# ── /maintenance on | off (owner/sudo, private chat only) ─────────────────
@bot.on_message(cdx("maintenance") & filters.private, group=1)
async def maintenance_toggle(client, message: Message):
    global MAINTENANCE_MODE

    if message.from_user is None or not _is_sudo(message.from_user.id):
        return await message.reply_text(
            "❌ Yeh command sirf bot owner/sudo users use kar sakte hain."
        )

    args = (message.text or "").split(None, 1)
    if len(args) < 2:
        status = "ON ✅" if MAINTENANCE_MODE else "OFF ❌"
        return await message.reply_text(
            f"🛠 **Maintenance Mode:** {status}\n\n"
            "Usage:\n"
            "`/maintenance on` - Maintenance mode chalu karein\n"
            "`/maintenance off` - Maintenance mode band karein"
        )

    state = args[1].strip().lower()

    if state in ("on", "true", "enable", "1"):
        MAINTENANCE_MODE = True
        await message.reply_text(
            "✅ **Maintenance mode ON kar diya gaya hai.**\n"
            "Ab sirf owner/sudo users hi bot use kar sakte hain."
        )
    elif state in ("off", "false", "disable", "0"):
        MAINTENANCE_MODE = False
        await message.reply_text(
            "✅ **Maintenance mode OFF kar diya gaya hai.**\n"
            "Bot ab normal kaam karega."
        )
    else:
        await message.reply_text(
            "⚠️ Galat usage. `/maintenance on` ya `/maintenance off` use karein."
        )


# ── Global blocker — sabse pehle (group=-1) ───────────────────────────────
@bot.on_message(filters.text, group=-1)
async def maintenance_blocker(client, message: Message):
    if not MAINTENANCE_MODE:
        raise ContinuePropagation

    text = message.text or ""
    if not text.startswith(PREFIXES):
        raise ContinuePropagation

    if message.from_user and _is_sudo(message.from_user.id):
        raise ContinuePropagation

    # allow /maintenance itself for non-sudo only to show status? No — only sudo can use it.
    # Still block all other commands for normal users.
    try:
        cmd = text.split()[0][1:].split("@")[0].lower()
    except Exception:
        cmd = ""

    if cmd == "maintenance":
        # non-sudo tries /maintenance → still block with maintenance msg
        # (toggle handler is private+sudo only)
        await message.reply_text(MAINTENANCE_MSG)
        raise StopPropagation

    await message.reply_text(MAINTENANCE_MSG)
    raise StopPropagation
