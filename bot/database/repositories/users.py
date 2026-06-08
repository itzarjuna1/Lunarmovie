from datetime import datetime, timezone
from typing import Optional

from bot.database.client import get_db
from bot.database.models import User


class UserRepository:
    _col = "users"

    @classmethod
    def _coll(cls):
        return get_db()[cls._col]

    @classmethod
    async def get_or_create(cls, user_id: int, first_name: str, username: Optional[str] = None) -> dict:
        coll = cls._coll()
        doc = await coll.find_one({"user_id": user_id})
        if doc:
            return doc
        user = User(user_id=user_id, first_name=first_name, username=username)
        await coll.insert_one(user.model_dump())
        return user.model_dump()

    @classmethod
    async def get(cls, user_id: int) -> Optional[dict]:
        return await cls._coll().find_one({"user_id": user_id})

    @classmethod
    async def count(cls) -> int:
        return await cls._coll().count_documents({})

    @classmethod
    async def is_banned(cls, user_id: int) -> bool:
        doc = await get_db()["banned_users"].find_one({"user_id": user_id})
        return doc is not None

    @classmethod
    async def ban(cls, user_id: int, reason: str = "") -> None:
        await get_db()["banned_users"].update_one(
            {"user_id": user_id},
            {"$set": {"user_id": user_id, "reason": reason, "banned_at": datetime.now(timezone.utc)}},
            upsert=True,
        )

    @classmethod
    async def unban(cls, user_id: int) -> bool:
        result = await get_db()["banned_users"].delete_one({"user_id": user_id})
        return result.deleted_count > 0

    @classmethod
    async def is_admin(cls, user_id: int) -> bool:
        doc = await get_db()["admins"].find_one({"user_id": user_id})
        return doc is not None

    @classmethod
    async def add_admin(cls, user_id: int) -> None:
        await get_db()["admins"].update_one(
            {"user_id": user_id},
            {"$set": {"user_id": user_id, "added_at": datetime.now(timezone.utc)}},
            upsert=True,
        )

    @classmethod
    async def remove_admin(cls, user_id: int) -> bool:
        result = await get_db()["admins"].delete_one({"user_id": user_id})
        return result.deleted_count > 0

    @classmethod
    async def add_to_history(cls, user_id: int, query: str) -> None:
        await cls._coll().update_one(
            {"user_id": user_id},
            {"$push": {"search_history": {"$each": [query], "$slice": -50}}},
        )

    @classmethod
    async def add_to_watchlist(cls, user_id: int, movie_title: str) -> None:
        await cls._coll().update_one(
            {"user_id": user_id},
            {"$addToSet": {"watchlist": movie_title}},
        )

    @classmethod
    async def add_to_favorites(cls, user_id: int, movie_title: str) -> None:
        await cls._coll().update_one(
            {"user_id": user_id},
            {"$addToSet": {"favorites": movie_title}},
        )

    @classmethod
    async def get_all_ids(cls) -> list[int]:
        docs = await cls._coll().find({}, {"user_id": 1}).to_list(length=None)
        return [d["user_id"] for d in docs]
