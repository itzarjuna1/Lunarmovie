import os
from dataclasses import dataclass, field
from typing import List

from dotenv import load_dotenv

load_dotenv()


def _parse_int_list(env_var: str) -> List[int]:
    raw = os.getenv(env_var, "")
    return [int(x.strip()) for x in raw.split(",") if x.strip().lstrip("-").isdigit()]


@dataclass
class Config:
    # ── Bot credentials ──────────────────────────────────────────────────────
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    API_ID: int = int(os.getenv("API_ID", "0"))
    API_HASH: str = os.getenv("API_HASH", "")
    BOT_USERNAME: str = os.getenv("BOT_USERNAME", "LunarMovieBot")

    # ── MongoDB ───────────────────────────────────────────────────────────────
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "lunar_movie_bot")

    # ── TMDb ─────────────────────────────────────────────────────────────────
    TMDB_API_KEY: str = os.getenv("TMDB_API_KEY", "")
    TMDB_BASE_URL: str = "https://api.themoviedb.org/3"
    TMDB_IMAGE_BASE_URL: str = "https://image.tmdb.org/t/p"

    # ── Channels ──────────────────────────────────────────────────────────────
    STORAGE_CHANNELS: List[int] = field(
        default_factory=lambda: _parse_int_list("STORAGE_CHANNELS")
    )
    LOG_CHANNEL: int = int(os.getenv("LOG_CHANNEL", "0"))

    # ── Admins ────────────────────────────────────────────────────────────────
    ADMINS: List[int] = field(
        default_factory=lambda: _parse_int_list("ADMINS")
    )

    # ── Rate limiting & behavior ──────────────────────────────────────────────
    MAX_RESULTS: int = int(os.getenv("MAX_RESULTS", "10"))
    AUTO_DELETE_TIMEOUT: int = int(os.getenv("AUTO_DELETE_TIMEOUT", "300"))
    FLOOD_WAIT_SECONDS: int = int(os.getenv("FLOOD_WAIT_SECONDS", "2"))
    MAX_REQUESTS_PER_MINUTE: int = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "20"))

    # ── Misc ──────────────────────────────────────────────────────────────────
    WELCOME_IMAGE: str = os.getenv(
        "WELCOME_IMAGE",
        "https://images.pexels.com/photos/7991579/pexels-photo-7991579.jpeg",
    )
    SUPPORT_CHAT: str = os.getenv("SUPPORT_CHAT", "")


config = Config()
