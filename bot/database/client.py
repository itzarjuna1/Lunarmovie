from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from bot.configs import config
from bot.utils.logger import log

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect() -> AsyncIOMotorDatabase:
    global _client, _db
    _client = AsyncIOMotorClient(config.MONGODB_URI)
    _db = _client[config.DB_NAME]
    await _ensure_indexes(_db)
    log.info("Connected to MongoDB — database: %s", config.DB_NAME)
    return _db


async def disconnect() -> None:
    global _client
    if _client:
        _client.close()
        log.info("MongoDB connection closed")


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Database not initialised — call connect() first")
    return _db


async def _ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    movies = db["movies"]
    await movies.create_index([("title", "text"), ("caption", "text")])
    await movies.create_index([("file_unique_id", 1)], unique=True)
    await movies.create_index([("year", 1)])
    await movies.create_index([("quality", 1)])
    await movies.create_index([("language", 1)])
    await movies.create_index([("storage_channel_id", 1), ("message_id", 1)])
    await movies.create_index([("upload_date", -1)])

    users = db["users"]
    await users.create_index([("user_id", 1)], unique=True)
    await users.create_index([("joined_date", -1)])

    requests = db["requests"]
    await requests.create_index([("user_id", 1)])
    await requests.create_index([("title", "text")])
    await requests.create_index([("status", 1)])

    banned = db["banned_users"]
    await banned.create_index([("user_id", 1)], unique=True)

    admins = db["admins"]
    await admins.create_index([("user_id", 1)], unique=True)

    log.debug("MongoDB indexes ensured")
