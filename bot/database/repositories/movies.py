import re
from typing import Any, Optional

from bot.database.client import get_db
from bot.database.models import Movie


class MovieRepository:
    _col = "movies"

    @classmethod
    def _coll(cls):
        return get_db()[cls._col]

    # ── Write ─────────────────────────────────────────────────────────────────

    @classmethod
    async def upsert(cls, movie: Movie) -> bool:
        """Insert or update by file_unique_id. Returns True on insert."""
        coll = cls._coll()
        doc = movie.model_dump()
        result = await coll.update_one(
            {"file_unique_id": movie.file_unique_id},
            {"$set": doc},
            upsert=True,
        )
        return result.upserted_id is not None

    @classmethod
    async def delete_by_unique_id(cls, file_unique_id: str) -> bool:
        result = await cls._coll().delete_one({"file_unique_id": file_unique_id})
        return result.deleted_count > 0

    @classmethod
    async def delete_by_channel_message(
        cls, channel_id: int, message_id: int
    ) -> bool:
        result = await cls._coll().delete_one(
            {"storage_channel_id": channel_id, "message_id": message_id}
        )
        return result.deleted_count > 0

    # ── Read ──────────────────────────────────────────────────────────────────

    @classmethod
    async def search(
        cls,
        query: str,
        page: int = 1,
        page_size: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> tuple[list[dict], int]:
        """Full-text + regex search with pagination. Returns (results, total)."""
        coll = cls._coll()

        # Build query
        search_filter: dict[str, Any] = {}
        if filters:
            search_filter.update(filters)

        # Try exact text index first
        text_filter = {**search_filter, "$text": {"$search": query}}
        total = await coll.count_documents(text_filter)

        if total == 0:
            # Fallback to regex (case-insensitive, partial)
            escaped = re.escape(query)
            regex_filter = {
                **search_filter,
                "movie_title": {"$regex": escaped, "$options": "i"},
            }
            total = await coll.count_documents(regex_filter)
            cursor = coll.find(regex_filter)
        else:
            cursor = coll.find(
                text_filter,
                {"score": {"$meta": "textScore"}},
            ).sort([("score", {"$meta": "textScore"})])

        skip = (page - 1) * page_size
        docs = await cursor.skip(skip).limit(page_size).to_list(length=page_size)
        return docs, total

    @classmethod
    async def find_by_unique_id(cls, file_unique_id: str) -> Optional[dict]:
        return await cls._coll().find_one({"file_unique_id": file_unique_id})

    @classmethod
    async def get_recent(cls, limit: int = 10) -> list[dict]:
        return (
            await cls._coll()
            .find()
            .sort("upload_date", -1)
            .limit(limit)
            .to_list(length=limit)
        )

    @classmethod
    async def get_by_quality(cls, quality: str, limit: int = 10) -> list[dict]:
        return (
            await cls._coll()
            .find({"quality": {"$regex": quality, "$options": "i"}})
            .limit(limit)
            .to_list(length=limit)
        )

    @classmethod
    async def count_all(cls) -> int:
        return await cls._coll().count_documents({})

    @classmethod
    async def delete_by_channel(cls, channel_id: int) -> int:
        result = await cls._coll().delete_many(
            {"storage_channel_id": channel_id}
        )
        return result.deleted_count
