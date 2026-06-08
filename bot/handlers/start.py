from pyrogram import Client, filters
from pyrogram.types import Message

from bot.configs import config
from bot.database.repositories.users import UserRepository
from bot.filters import banned_filter
from bot.modules import main_menu
from bot.utils.decorators import log_errors

WELCOME_TEXT = """
🌙 **Welcome to Lunar Movie Client!**

I'm your personal movie search assistant. Search for any movie and I'll find it for you!

**What I can do:**
• 🔍 Search movies by name
• 🎬 Get TMDb metadata — poster, cast, trailer & more
• ⬇️ Direct download via Telegram file links
• 🌐 Internet Archive fallback for public-domain films
• 📋 Watchlist, Favorites & Request system

**How to search:**
• Type `/movie <title>` or just send the movie name
• Use inline mode: `@{username} <title>`

Hit a button below to get started 👇
""".strip()


@Client.on_message(filters.command("start") & filters.private & ~banned_filter)
@log_errors
async def start_handler(client: Client, message: Message) -> None:
    user = message.from_user
    await UserRepository.get_or_create(
        user.id,
        user.first_name,
        user.username,
    )
    await message.reply_photo(
        photo=config.WELCOME_IMAGE,
        caption=WELCOME_TEXT.format(username=config.BOT_USERNAME),
        reply_markup=main_menu(),
    )


@Client.on_message(filters.command("help") & filters.private & ~banned_filter)
@log_errors
async def help_handler(client: Client, message: Message) -> None:
    help_text = """
**Lunar Movie Client — Help**

**User Commands:**
`/start` — Main menu
`/movie <title>` — Search a movie
`/trending` — Today's trending movies
`/recent` — Recently added movies
`/watchlist` — Your watchlist
`/favorites` — Your favorites
`/history` — Your search history
`/request <title>` — Request a movie
`/myrequests` — View your requests

**Inline Mode:**
`@{username} <movie title>` — Search inline from any chat

**Tips:**
• Results show available qualities; tap Download to receive the file.
• If a file is not indexed, you'll get Internet Archive links.
""".strip()
    await message.reply(help_text.format(username=config.BOT_USERNAME))
