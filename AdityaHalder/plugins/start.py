import random

from .. import bot, cdx, rgx, console
from ..modules.database import add_served_user

from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup 



@bot.on_message(cdx(["start", "help"]) & ~filters.private)
async def start_message_private(client, message):
    await add_served_user(message.from_user.id)
    mention = message.from_user.mention
    start_messages = [
        """**🎵 Thanks for getting me started!**

I am a **high-quality**, ⚡ **simple** and 🚀
fast music bot.

To enjoy the 🎧 **highest quality audio/
video**, click the 📌 **button below** and
add me to your group now.

You can 📚 **learn about all my
commands** and their functions by
clicking on the 📝 **command menu**
button below.""",
        f"""🎵 **Hey there! {mention}**

I’m your 🎧 **high-quality**, ⚡ **fast**, and
🚀 **easy-to-use** music bot.

Enjoy crystal-clear 🎶 audio and
🎥 video — just 📌 **tap below** to add
me to your group!

📚 **Need help?** Check the 📝 **command
menu** for all my features.""",
    ]
    photo = console.START_IMAGE_URL
    caption = random.choice(start_messages)
    buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="➕ Add Me To Your Group 💬",
                        url=f"https://t.me/{client.me.username}?startgroup=true",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="📝 Open Command Menu ⚡",
                        callback_data="help_menu",
                    ),
                ]
            ]
    )
    await message.reply_photo(photo=photo, caption=caption, reply_markup=buttons)
    full_name = message.from_user.first_name + " " + (message.from_user.last_name or "")
    username = f"@{message.from_user.username}" if message.from_user.username else "N/A"
    user_id = message.from_user.id
    log_message = f"""
🚀 **{mention} Just Started the Bot!**

🧑 **Full Name:** {full_name}
🔗 **Username:** {username}
🆔 **Telegram ID:** `{user_id}`"""
    await client.send_message(console.LOG_GROUP_ID, text=log_message, disable_web_page_preview=True)



@bot.on_callback_query(rgx("help_menu"))
async def help_menu_cb(client, query):
    help_text = """🎶 **Music Bot Commands** 🎶

🎵 **/play** – Play audio song by **query**
or by **replying to an audio file.**
🎞️ **/vplay** - Play video song by **query**
or by **replying to an video file.**
⏸️ **/pause** – Pause the current song.
▶️ **/resume** – Resume the paused
song.
⏭️ **/skip** – Skip to the next track in
the queue.
🛑 **/end** – Stop playback and clear
the queue.

📊 **/stats** - Show system statistics.

🎦 **/active** - Show active chats. (Only owner can use this command)
📶 **/broadcast** - Broadcast a text or message to served chats/users. (Only owner can use this command)

💡 **Tip:** You can use /play with a song
name or link for best results!"""
    buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="➕ Add Me To Your Group 💬",
                        url=f"https://t.me/{client.me.username}?startgroup=true",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Go Back To Main Menu ✨",
                        callback_data="home_menu",
                    ),
                ]
            ]
    )
    await query.message.edit(help_text, reply_markup=buttons)




@bot.on_callback_query(rgx("home_menu"))
async def home_menu_cb(client, query):
    mention = query.from_user.mention
    start_messages = [
        """**🎵 Thanks for getting me started!**

I am a **high-quality**, ⚡ **simple** and 🚀
fast music bot.

To enjoy the 🎧 **highest quality audio/
video**, click the 📌 **button below** and
add me to your group now.

You can 📚 **learn about all my
commands** and their functions by
clicking on the 📝 **command menu**
button below.""",
        f"""🎵 **Hey there! {mention}**

I’m your 🎧 **high-quality**, ⚡ **fast**, and
🚀 **easy-to-use** music bot.

Enjoy crystal-clear 🎶 audio and
🎥 video — just 📌 **tap below** to add
me to your group!

📚 **Need help?** Check the 📝 **command
menu** for all my features.""",
    ]
    caption = random.choice(start_messages)
    buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="➕ Add Me To Your Group 💬",
                        url=f"https://t.me/{client.me.username}?startgroup=true",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="📝 Open Command Menu ⚡",
                        callback_data="help_menu",
                    ),
                ]
            ]
    )
    await query.message.edit(caption, reply_markup=buttons)









