from math import ceil

from pyrogram import Client, filters
from pyrogram.types import Message

from bot.configs import config
from bot.database.repositories.users import UserRepository
from bot.filters import banned_filter
from bot.modules import (
    build_movie_card,
    build_simple_card,
    movie_actions,
    search_results_keyboard,
)
from bot.services import search_engine, tmdb
from bot.utils.decorators import log_errors, rate_limit


# ── /movie command & plain-text DM search ────────────────────────────────────

@Client.on_message(
    (filters.command("movie") | (filters.text & filters.private))
    & ~filters.command(["start", "help", "trending", "recent", "watchlist",
                         "favorites", "history", "request", "myrequests",
                         "stats", "broadcast", "users", "requests", "ban",
                         "unban", "reindex", "addadmin", "removeadmin", "logs",
                         "admin"])
    & ~banned_filter
)
@rate_limit
@log_errors
async def search_handler(client: Client, message: Message) -> None:
    if message.command:
        query = " ".join(message.command[1:]).strip()
    else:
        query = (message.text or "").strip()

    if not query:
        await message.reply("Please provide a movie name.\nExample: `/movie Inception`")
        return

    # Update history
    if message.from_user:
        await UserRepository.add_to_history(message.from_user.id, query)

    status_msg = await message.reply("🔍 Searching...")

    results, total = await search_engine.search(query, page=1, page_size=config.MAX_RESULTS)

    if not results:
        # Suggest requesting
        await status_msg.edit_text(
            f"No results found for **{query}**.\n\n"
            "Use `/request " + query + "` to request this movie.",
        )
        return

    if total == 1:
        await _show_movie_detail(client, status_msg, results[0], query, 1, 0, 1)
        return

    total_pages = ceil(total / config.MAX_RESULTS)
    text = f"🎬 Found **{total}** result(s) for `{query}`\n\nChoose a result:"
    await status_msg.edit_text(
        text,
        reply_markup=search_results_keyboard(
            results, query, 1, total, config.MAX_RESULTS
        ),
    )


# ── /trending ─────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("trending") & ~banned_filter)
@log_errors
async def trending_handler(client: Client, message: Message) -> None:
    movies = await tmdb.get_trending()
    if not movies:
        await message.reply("Could not fetch trending movies. Try again later.")
        return
    lines = ["🔥 **Trending This Week:**\n"]
    for i, m in enumerate(movies[:10], 1):
        title = m.get("title", "?")
        year = (m.get("release_date") or "")[:4]
        rating = round(m.get("vote_average", 0), 1)
        lines.append(f"{i}. **{title}** ({year}) ⭐ {rating}")
    await message.reply("\n".join(lines))


# ── /recent ───────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("recent") & ~banned_filter)
@log_errors
async def recent_handler(client: Client, message: Message) -> None:
    from bot.database.repositories.movies import MovieRepository

    docs = await MovieRepository.get_recent(10)
    if not docs:
        await message.reply("No movies indexed yet.")
        return
    lines = ["🆕 **Recently Added:**\n"]
    for m in docs:
        lines.append(f"• {build_simple_card(m)}")
    await message.reply("\n\n".join(lines))


# ── Watchlist / Favorites ─────────────────────────────────────────────────────

@Client.on_message(filters.command("watchlist") & filters.private & ~banned_filter)
@log_errors
async def watchlist_handler(client: Client, message: Message) -> None:
    user = await UserRepository.get(message.from_user.id)
    wl = (user or {}).get("watchlist", [])
    if not wl:
        await message.reply("Your watchlist is empty. Use the watchlist button on movie cards.")
        return
    text = "📋 **Your Watchlist:**\n\n" + "\n".join(f"• {t}" for t in wl)
    await message.reply(text)


@Client.on_message(filters.command("favorites") & filters.private & ~banned_filter)
@log_errors
async def favorites_handler(client: Client, message: Message) -> None:
    user = await UserRepository.get(message.from_user.id)
    fav = (user or {}).get("favorites", [])
    if not fav:
        await message.reply("No favorites yet. Tap ❤️ on any movie card.")
        return
    text = "❤️ **Your Favorites:**\n\n" + "\n".join(f"• {t}" for t in fav)
    await message.reply(text)


@Client.on_message(filters.command("history") & filters.private & ~banned_filter)
@log_errors
async def history_handler(client: Client, message: Message) -> None:
    user = await UserRepository.get(message.from_user.id)
    hist = (user or {}).get("search_history", [])[-20:]
    if not hist:
        await message.reply("No search history yet.")
        return
    text = "📜 **Recent Searches:**\n\n" + "\n".join(f"• `{q}`" for q in reversed(hist))
    await message.reply(text)


# ── Internal helper ───────────────────────────────────────────────────────────

async def _show_movie_detail(
    client: Client,
    message: Message,
    db_movie: dict,
    query: str,
    page: int,
    result_index: int,
    total_results: int,
) -> None:
    title = db_movie.get("movie_title", query)
    year = db_movie.get("year")
    fuid = db_movie.get("file_unique_id")

    meta = await tmdb.enrich(title, year)
    if meta:
        card = build_movie_card(meta, db_movie)
        poster = meta.get("poster_url")
        trailer_key = meta.get("trailer_key")
        tmdb_id = meta.get("tmdb_id")
        similar = bool(meta.get("similar"))
    else:
        card = build_simple_card(db_movie)
        poster = None
        trailer_key = None
        tmdb_id = None
        similar = False

    kb = movie_actions(
        file_unique_id=fuid,
        tmdb_id=tmdb_id,
        trailer_key=trailer_key,
        query=query,
        page=page,
        result_index=result_index,
        total_pages=total_results,
        has_similar=similar,
    )

    if poster:
        await message.delete()
        await client.send_photo(
            message.chat.id,
            photo=poster,
            caption=card,
            reply_markup=kb,
        )
    else:
        await message.edit_text(card, reply_markup=kb)
