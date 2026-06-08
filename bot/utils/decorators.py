import asyncio
import functools
from collections import defaultdict
from datetime import datetime, timezone
from typing import Callable

from pyrogram.types import Message

from bot.configs import config
from bot.utils.logger import log

# ── Simple in-process rate limiter ───────────────────────────────────────────
_rate_store: dict[int, list[float]] = defaultdict(list)


def rate_limit(func: Callable) -> Callable:
    """Silently drop messages that exceed MAX_REQUESTS_PER_MINUTE."""

    @functools.wraps(func)
    async def wrapper(client, message: Message, *args, **kwargs):
        uid = message.from_user.id if message.from_user else 0
        now = asyncio.get_event_loop().time()
        window = config.FLOOD_WAIT_SECONDS * 60  # 1-minute window approximation

        _rate_store[uid] = [t for t in _rate_store[uid] if now - t < 60]
        if len(_rate_store[uid]) >= config.MAX_REQUESTS_PER_MINUTE:
            await message.reply(
                "You are sending too many requests. Please wait a moment.",
                quote=True,
            )
            return
        _rate_store[uid].append(now)
        return await func(client, message, *args, **kwargs)

    return wrapper


def admin_required(func: Callable) -> Callable:
    """Block non-admins from executing the handler."""

    @functools.wraps(func)
    async def wrapper(client, message: Message, *args, **kwargs):
        from bot.database.repositories.users import UserRepository

        uid = message.from_user.id if message.from_user else 0
        is_admin = uid in config.ADMINS or await UserRepository.is_admin(uid)
        if not is_admin:
            await message.reply("You are not authorized to use this command.")
            return
        return await func(client, message, *args, **kwargs)

    return wrapper


def log_errors(func: Callable) -> Callable:
    """Catch and log unexpected exceptions without crashing the bot."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as exc:
            log.exception("Unhandled error in %s: %s", func.__qualname__, exc)

    return wrapper
