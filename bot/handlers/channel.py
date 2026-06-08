from pyrogram import Client, filters
from pyrogram.types import Message, Video, Document

from bot.configs import config
from bot.database.repositories.movies import MovieRepository
from bot.database.models import Movie
from bot.modules.file_parser import parse_filename
from bot.utils.decorators import log_errors
from bot.utils.logger import log


def _is_storage_channel(_, __, message: Message) -> bool:
    return message.chat.id in config.STORAGE_CHANNELS


storage_channel_filter = filters.create(_is_storage_channel)


@Client.on_message(storage_channel_filter & (filters.video | filters.document))
@log_errors
async def channel_index_handler(client: Client, message: Message) -> None:
    media: Video | Document | None = message.video or message.document
    if not media:
        return

    # Only index video documents
    if isinstance(media, Document):
        mime = getattr(media, "mime_type", "") or ""
        if not mime.startswith("video/"):
            return

    filename = (
        getattr(media, "file_name", None)
        or message.caption
        or f"movie_{message.id}"
    )
    parsed = parse_filename(filename)
    log.info(
        "Indexing: %s | quality=%s year=%s lang=%s channel=%s msg=%s",
        parsed.title, parsed.quality, parsed.year, parsed.language,
        message.chat.id, message.id,
    )

    movie = Movie(
        file_id=media.file_id,
        file_unique_id=media.file_unique_id,
        movie_title=parsed.title,
        year=parsed.year,
        language=parsed.language,
        quality=parsed.quality,
        codec=parsed.codec,
        size=getattr(media, "file_size", None),
        duration=getattr(media, "duration", None),
        caption=message.caption or "",
        storage_channel_id=message.chat.id,
        message_id=message.id,
    )

    inserted = await MovieRepository.upsert(movie)
    if config.LOG_CHANNEL:
        status = "Indexed" if inserted else "Updated"
        try:
            await client.send_message(
                config.LOG_CHANNEL,
                f"📁 **{status}:** `{parsed.title}` "
                f"({parsed.year or 'N/A'}) | {parsed.quality or 'N/A'} | "
                f"channel={message.chat.id} msg={message.id}",
            )
        except Exception:
            pass


@Client.on_message(storage_channel_filter & filters.service)
@log_errors
async def channel_delete_handler(client: Client, message: Message) -> None:
    """Remove indexed record when a storage-channel message is deleted."""
    if not hasattr(message, "deleted_messages"):
        return
    for mid in getattr(message, "deleted_messages", []):
        await MovieRepository.delete_by_channel_message(message.chat.id, mid)
