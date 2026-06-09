from pyrogram import Client

from bot.configs import config

app = Client(
    "lunar_movie_bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    workdir="sessions",
)
