from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Movie(BaseModel):
    file_id: str
    file_unique_id: str
    movie_title: str
    year: Optional[int] = None
    language: Optional[str] = None
    quality: Optional[str] = None
    codec: Optional[str] = None
    size: Optional[int] = None          # bytes
    duration: Optional[int] = None     # seconds
    caption: Optional[str] = None
    storage_channel_id: int
    message_id: int
    upload_date: datetime = Field(default_factory=_now)
    tmdb_id: Optional[int] = None


class User(BaseModel):
    user_id: int
    first_name: str
    username: Optional[str] = None
    joined_date: datetime = Field(default_factory=_now)
    is_banned: bool = False
    search_history: list[str] = Field(default_factory=list)
    watchlist: list[str] = Field(default_factory=list)
    favorites: list[str] = Field(default_factory=list)


class MovieRequest(BaseModel):
    user_id: int
    title: str
    year: Optional[int] = None
    requested_at: datetime = Field(default_factory=_now)
    status: str = "pending"   # pending | fulfilled | rejected
    fulfilled_by: Optional[int] = None
    fulfilled_at: Optional[datetime] = None
