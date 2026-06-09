"""
Lunar Movie Client — entry point.
Run with: python -m bot.main
"""
import asyncio
import signal

from bot.former import app
from bot.configs import config
from bot.database import connect, disconnect
from bot.utils.logger import log

# Register handlers
import bot.handlers.start      # noqa: F401
import bot.handlers.search     # noqa: F401
import bot.handlers.admin      # noqa: F401
import bot.handlers.callbacks  # noqa: F401
import bot.handlers.inline     # noqa: F401
import bot.handlers.channel    # noqa: F401
import bot.handlers.request    # noqa: F401


async def main() -> None:
    log.info("Starting Lunar Movie Client…")
    await connect()

    stop_event = asyncio.Event()

    def _signal_handler(*_):
        log.info("Shutdown signal received")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, _signal_handler)

    async with app:
        log.info("Bot is running — @%s", config.BOT_USERNAME)
        await stop_event.wait()

    from bot.services import tmdb, archive

    await tmdb.close()
    await archive.close()
    await disconnect()

    log.info("Lunar Movie Client stopped cleanly.")


if __name__ == "__main__":
    asyncio.run(main())
