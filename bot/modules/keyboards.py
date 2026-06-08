from math import ceil
from typing import Optional

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


# ── Main menu ─────────────────────────────────────────────────────────────────

def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎬 Search Movie", switch_inline_query_current_chat=""),
            InlineKeyboardButton("🔥 Trending", callback_data="trending"),
        ],
        [
            InlineKeyboardButton("🆕 Recently Added", callback_data="recent"),
            InlineKeyboardButton("🎭 By Genre", callback_data="genres"),
        ],
        [
            InlineKeyboardButton("📋 My Watchlist", callback_data="watchlist"),
            InlineKeyboardButton("❤️ Favorites", callback_data="favorites"),
        ],
        [
            InlineKeyboardButton("📜 History", callback_data="history"),
            InlineKeyboardButton("📩 Requests", callback_data="my_requests"),
        ],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")],
    ])


# ── Movie detail card buttons ─────────────────────────────────────────────────

def movie_actions(
    file_unique_id: Optional[str],
    tmdb_id: Optional[int],
    trailer_key: Optional[str],
    query: str,
    page: int,
    result_index: int,
    total_pages: int,
    has_similar: bool = False,
    request_id: Optional[str] = None,
) -> InlineKeyboardMarkup:
    rows = []

    if file_unique_id:
        rows.append([
            InlineKeyboardButton("⬇️ Download", callback_data=f"dl|{file_unique_id}"),
            InlineKeyboardButton("📦 Qualities", callback_data=f"qualities|{file_unique_id}"),
        ])
    else:
        rows.append([
            InlineKeyboardButton("🌐 Archive Links", callback_data=f"archive|{query}"),
        ])

    if trailer_key:
        rows.append([
            InlineKeyboardButton("▶️ Trailer", url=f"https://www.youtube.com/watch?v={trailer_key}"),
        ])

    if tmdb_id and has_similar:
        rows.append([
            InlineKeyboardButton("🎥 Similar Movies", callback_data=f"similar|{tmdb_id}"),
        ])

    nav = _pagination_row(query, page, total_pages, result_index)
    if nav:
        rows.append(nav)

    rows.append([
        InlineKeyboardButton("❤️ Favorite", callback_data=f"fav|{query}"),
        InlineKeyboardButton("📋 Watchlist", callback_data=f"watch|{query}"),
        InlineKeyboardButton("🏠 Home", callback_data="home"),
    ])

    return InlineKeyboardMarkup(rows)


def _pagination_row(
    query: str, page: int, total_pages: int, result_index: int
) -> list[InlineKeyboardButton] | None:
    row = []
    if result_index > 0:
        row.append(InlineKeyboardButton("◀ Prev", callback_data=f"nav|{query}|{page}|{result_index - 1}"))
    row.append(InlineKeyboardButton(f"{result_index + 1}/{total_pages}", callback_data="noop"))
    if result_index < total_pages - 1:
        row.append(InlineKeyboardButton("Next ▶", callback_data=f"nav|{query}|{page}|{result_index + 1}"))
    return row if len(row) > 1 else None


# ── Search results list ───────────────────────────────────────────────────────

def search_results_keyboard(
    results: list[dict], query: str, page: int, total: int, page_size: int
) -> InlineKeyboardMarkup:
    rows = []
    for i, r in enumerate(results):
        title = r.get("movie_title", "Unknown")
        year = r.get("year", "")
        quality = r.get("quality", "")
        label = f"{title} ({year}) {quality}".strip()
        fuid = r.get("file_unique_id", "")
        rows.append([
            InlineKeyboardButton(label, callback_data=f"view|{fuid}|{query}|{page}|{i}")
        ])

    nav = []
    total_pages = ceil(total / page_size)
    if page > 1:
        nav.append(InlineKeyboardButton("◀ Prev", callback_data=f"page|{query}|{page - 1}"))
    if page < total_pages:
        nav.append(InlineKeyboardButton("Next ▶", callback_data=f"page|{query}|{page + 1}"))
    if nav:
        rows.append(nav)

    rows.append([
        InlineKeyboardButton("🔍 New Search", switch_inline_query_current_chat=""),
        InlineKeyboardButton("🏠 Home", callback_data="home"),
    ])
    return InlineKeyboardMarkup(rows)


# ── Request / Notify ──────────────────────────────────────────────────────────

def request_buttons(request_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Fulfill", callback_data=f"fulfill|{request_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject|{request_id}"),
        ]
    ])


# ── Genre list ────────────────────────────────────────────────────────────────

GENRES = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy",
    80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family",
    14: "Fantasy", 36: "History", 27: "Horror", 10402: "Music",
    9648: "Mystery", 10749: "Romance", 878: "Sci-Fi", 10770: "TV Movie",
    53: "Thriller", 10752: "War", 37: "Western",
}


def genres_keyboard() -> InlineKeyboardMarkup:
    items = list(GENRES.items())
    rows = [
        [
            InlineKeyboardButton(items[i][1], callback_data=f"genre|{items[i][0]}"),
            InlineKeyboardButton(items[i + 1][1], callback_data=f"genre|{items[i + 1][0]}"),
        ]
        for i in range(0, len(items) - 1, 2)
    ]
    rows.append([InlineKeyboardButton("🏠 Back", callback_data="home")])
    return InlineKeyboardMarkup(rows)


# ── Admin ─────────────────────────────────────────────────────────────────────

def admin_panel() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
            InlineKeyboardButton("📋 Requests", callback_data="admin_requests"),
        ],
        [
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
            InlineKeyboardButton("👥 Users", callback_data="admin_users"),
        ],
        [
            InlineKeyboardButton("🔄 Reindex", callback_data="admin_reindex"),
        ],
    ])
