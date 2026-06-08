from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId

from bot.database.client import get_db
from bot.database.models import MovieRequest


class RequestRepository:
    _col = "requests"

    @classmethod
    def _coll(cls):
        return get_db()[cls._col]

    @classmethod
    async def create(cls, user_id: int, title: str, year: Optional[int] = None) -> str:
        req = MovieRequest(user_id=user_id, title=title, year=year)
        result = await cls._coll().insert_one(req.model_dump())
        return str(result.inserted_id)

    @classmethod
    async def get_pending(cls, limit: int = 20) -> list[dict]:
        return (
            await cls._coll()
            .find({"status": "pending"})
            .sort("requested_at", 1)
            .limit(limit)
            .to_list(length=limit)
        )

    @classmethod
    async def count_pending(cls) -> int:
        return await cls._coll().count_documents({"status": "pending"})

    @classmethod
    async def fulfill(cls, request_id: str, admin_id: int) -> bool:
        result = await cls._coll().update_one(
            {"_id": ObjectId(request_id)},
            {
                "$set": {
                    "status": "fulfilled",
                    "fulfilled_by": admin_id,
                    "fulfilled_at": datetime.now(timezone.utc),
                }
            },
        )
        return result.modified_count > 0

    @classmethod
    async def get_by_id(cls, request_id: str) -> Optional[dict]:
        return await cls._coll().find_one({"_id": ObjectId(request_id)})

    @classmethod
    async def get_user_requests(cls, user_id: int) -> list[dict]:
        return (
            await cls._coll()
            .find({"user_id": user_id})
            .sort("requested_at", -1)
            .limit(10)
            .to_list(length=10)
        )
