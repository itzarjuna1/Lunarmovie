from pyrogram import filters
from pyrogram.types import Message

from bot.configs import config
from bot.database.repositories.users import UserRepository


async def _is_admin(_, __, message: Message) -> bool:
    if not message.from_user:
        return False
    uid = message.from_user.id
    return uid in config.ADMINS or await UserRepository.is_admin(uid)


async def _is_banned(_, __, message: Message) -> bool:
    if not message.from_user:
        return False
    return await UserRepository.is_banned(message.from_user.id)


admin_filter = filters.create(_is_admin)
banned_filter = filters.create(_is_banned)
