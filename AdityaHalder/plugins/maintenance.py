from pyrogram import filters
from pyrogram.types import Message, CallbackQuery

try:
    from pyrogram import StopPropagation, ContinuePropagation
except ImportError:
    try:
        from pyrogram.errors import StopPropagation, ContinuePropagation
    except ImportError:

        class StopPropagation(Exception):
            pass

        class ContinuePropagation(Exception):
            pass

from .. import bot, cdx, console

# Shared state on console so every plugin sees same value
if not hasattr(console, "MAINTENANCE_MODE"):
    console.MAINTENANCE_MODE = False

MAINTENANCE_MSG = (
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
        sudoers = console.sudoers
        # filters.user() — check internal users set if present
        users = getattr(sudoers, "users", None) or getattr(sudoers, "user_ids", None)
        if users is not None:
            return user_id in users
        return user_id in sudoers
    except Exception:
        return False


def _is_command(text: str) -> bool:
    if not text:
        return False
    t = text.strip()
    return t.startswith(PREFIXES)


# ── /maintenance on | off (owner/sudo, private only) ──────────────────────
@bot.on_message(cdx("maintenance") & filters.private, group=1)
async def maintenance_toggle(client, message: Message):
    if message.from_user is None or not _is_sudo(message.from_user.id):
        return await message.reply_text(
            "❌ Yeh command sirf bot owner/sudo users use kar sakte hain."
        )

    args = (message.text or "").split(None, 1)
    if len(args) < 2:
        status = "ON ✅" if console.MAINTENANCE_MODE else "OFF ❌"
        return await message.reply_text(
            f"🛠 **Maintenance Mode:** {status}\n\n"
            "Usage:\n"
            "`/maintenance on` - Maintenance mode chalu karein\n"
            "`/maintenance off` - Maintenance mode band karein"
        )

    state = args[1].strip().lower()

    if state in ("on", "true", "enable", "1"):
        console.MAINTENANCE_MODE = True
        await message.reply_text(
            "✅ **Maintenance mode ON.**\n"
            "Ab sirf owner/sudo users hi bot use kar sakte hain."
        )
    elif state in ("off", "false", "disable", "0"):
        console.MAINTENANCE_MODE = False
        await message.reply_text(
            "✅ **Maintenance mode OFF.**\n"
            "Bot ab normal kaam karega."
        )
    else:
        await message.reply_text(
            "⚠️ Galat usage. `/maintenance on` ya `/maintenance off` use karein."
        )


# ── Global command blocker (runs FIRST) ───────────────────────────────────
@bot.on_message(filters.text & filters.incoming, group=-999)
async def maintenance_blocker(client, message: Message):
    if not getattr(console, "MAINTENANCE_MODE", False):
        return

    if not _is_command(message.text or ""):
        return

    uid = message.from_user.id if message.from_user else 0
    if _is_sudo(uid):
        return

    # allow nothing for normal users — even /maintenance
    try:
        await message.reply_text(MAINTENANCE_MSG)
    except Exception:
        pass

    raise StopPropagation


# ── Block inline button callbacks too ─────────────────────────────────────
@bot.on_callback_query(group=-999)
async def maintenance_callback_blocker(client, query: CallbackQuery):
    if not getattr(console, "MAINTENANCE_MODE", False):
        return

    uid = query.from_user.id if query.from_user else 0
    if _is_sudo(uid):
        return

    try:
        await query.answer("🛠 Bot under maintenance.", show_alert=True)
    except Exception:
        pass

    raise StopPropagation
