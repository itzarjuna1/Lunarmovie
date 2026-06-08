import asyncio
from math import ceil

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

from bot.configs import config
from bot.database.repositories.movies import MovieRepository
from bot.database.repositories.requests import RequestRepository
from bot.database.repositories.users import UserRepository
from bot.filters import banned_filter
from bot.modules import (
    build_movie_card,
    build_simple_card,
    format_size,
    genres_keyboard,
    main_menu,
    movie_actions,
    search_results_keyboard,
    GENRES,
)
from bot.services import archive, search_engine, tmdb
from bot.utils.decorators import log_errors


@Client.on_callback_query(~banned_filter)
@log_errors
async def callback_router(client: Client, query: CallbackQuery) -> None:
    data = query.data or ""

    # ── Navigation: view a specific result ───────────────────────────────────
    if data.startswith("view|"):
        _, fuid, q, page_s, idx_s = data.split("|", 4)
        await _show_detail_cb(client, query, fuid, q, int(page_s), int(idx_s))

    # ── Page navigation ───────────────────────────────────────────────────────
    elif data.startswith("page|"):
        _, q, page_s = data.split("|", 2)
        await _search_page_cb(client, query, q, int(page_s))

    # ── Within-result navigation ──────────────────────────────────────────────
    elif data.startswith("nav|"):
        _, q, page_s, idx_s = data.split("|", 3)
        results, total = await search_engine.search(q, page=int(page_s), page_size=config.MAX_RESULTS)
        idx = int(idx_s)
        if 0 <= idx < len(results):
            await _show_detail_cb(client, query, results[idx].get("file_unique_id", ""), q, int(page_s), idx, total)
        else:
            await query.answer("No more results.")

    # ── Download ──────────────────────────────────────────────────────────────
    elif data.startswith("dl|"):
        fuid = data.split("|", 1)[1]
        await _send_download(client, query, fuid)

    # ── Archive fallback ──────────────────────────────────────────────────────
    elif data.startswith("archive|"):
        title = data.split("|", 1)[1]
        await _archive_links(client, query, title)

    # ── Similar movies ────────────────────────────────────────────────────────
    elif data.startswith("similar|"):
        tmdb_id = int(data.split("|", 1)[1])
        await _similar_movies(client, query, tmdb_id)

    # ── Favorite / Watchlist ──────────────────────────────────────────────────
    elif data.startswith("fav|"):
        title = data.split("|", 1)[1]
        uid = query.from_user.id
        await UserRepository.add_to_favorites(uid, title)
        await query.answer("Added to favorites ❤️")

    elif data.startswith("watch|"):
        title = data.split("|", 1)[1]
        uid = query.from_user.id
        await UserRepository.add_to_watchlist(uid, title)
        await query.answer("Added to watchlist 📋")

    # ── Home ──────────────────────────────────────────────────────────────────
    elif data == "home":
        await query.message.delete()
        await client.send_photo(
            query.message.chat.id,
            photo=config.WELCOME_IMAGE,
            caption="🌙 **Lunar Movie Client** — Main Menu",
            reply_markup=main_menu(),
        )
        await query.answer()

    # ── Trending ──────────────────────────────────────────────────────────────
    elif data == "trending":
        await _trending_cb(client, query)

    # ── Recent ────────────────────────────────────────────────────────────────
    elif data == "recent":
        await _recent_cb(client, query)

    # ── Genres ────────────────────────────────────────────────────────────────
    elif data == "genres":
        await query.message.edit_text(
            "🎭 **Browse by Genre** — choose one:",
            reply_markup=genres_keyboard(),
        )
        await query.answer()

    elif data.startswith("genre|"):
        genre_id = int(data.split("|", 1)[1])
        await _genre_cb(client, query, genre_id)

    # ── Watchlist / Favorites / History ───────────────────────────────────────
    elif data in ("watchlist", "favorites", "history", "my_requests"):
        await _user_list_cb(client, query, data)

    # ── Help ──────────────────────────────────────────────────────────────────
    elif data == "help":
        await query.message.edit_text(
            "Send a movie name or use `/movie <title>` to search.",
        )
        await query.answer()

    # ── Noop ──────────────────────────────────────────────────────────────────
    elif data == "noop":
        await query.answer()

    # ── Admin callbacks (delegated) ───────────────────────────────────────────
    elif data.startswith("admin_") or data.startswith("fulfill|") or data.startswith("reject|"):
        from bot.handlers.admin import admin_callback
        await admin_callback(client, query)

    else:
        await query.answer("Unknown action.")


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _show_detail_cb(
    client: Client,
    query: CallbackQuery,
    fuid: str,
    q: str,
    page: int,
    idx: int,
    total: int | None = None,
) -> None:
    await query.answer()
    doc = await MovieRepository.find_by_unique_id(fuid)
    if not doc:
        await query.message.reply("File no longer available.")
        return

    if total is None:
        _, total = await search_engine.search(q, page=1, page_size=config.MAX_RESULTS)

    title = doc.get("movie_title", q)
    year = doc.get("year")
    meta = await tmdb.enrich(title, year)

    if meta:
        card = build_movie_card(meta, doc)
        poster = meta.get("poster_url")
        trailer_key = meta.get("trailer_key")
        tmdb_id = meta.get("tmdb_id")
        similar = bool(meta.get("similar"))
    else:
        card = build_simple_card(doc)
        poster = None
        trailer_key = None
        tmdb_id = None
        similar = False

    kb = movie_actions(
        file_unique_id=fuid,
        tmdb_id=tmdb_id,
        trailer_key=trailer_key,
        query=q,
        page=page,
        result_index=idx,
        total_pages=total,
        has_similar=similar,
    )

    if poster:
        try:
            await query.message.delete()
        except Exception:
            pass
        await client.send_photo(
            query.message.chat.id,
            photo=poster,
            caption=card,
            reply_markup=kb,
        )
    else:
        await query.message.edit_text(card, reply_markup=kb)


async def _search_page_cb(client: Client, query: CallbackQuery, q: str, page: int) -> None:
    await query.answer()
    results, total = await search_engine.search(q, page=page, page_size=config.MAX_RESULTS)
    if not results:
        await query.message.edit_text("No more results.")
        return
    await query.message.edit_text(
        f"🎬 Found **{total}** result(s) for `{q}` — Page {page}",
        reply_markup=search_results_keyboard(results, q, page, total, config.MAX_RESULTS),
    )


async def _send_download(client: Client, query: CallbackQuery, fuid: str) -> None:
    await query.answer("Sending file…")
    doc = await MovieRepository.find_by_unique_id(fuid)
    if not doc:
        await query.message.reply("File not found. It may have been removed.")
        return
    file_id = doc.get("file_id")
    caption = f"🎬 **{doc.get('movie_title', 'Movie')}**\n"
    caption += f"📦 {doc.get('quality', 'N/A')} | {format_size(doc.get('size'))}"

    sent = await client.send_document(
        query.message.chat.id,
        document=file_id,
        caption=caption,
    )

    if config.AUTO_DELETE_TIMEOUT > 0:
        await asyncio.sleep(config.AUTO_DELETE_TIMEOUT)
        try:
            await sent.delete()
        except Exception:
            pass


async def _archive_links(client: Client, query: CallbackQuery, title: str) -> None:
    await query.answer("Searching Internet Archive…")
    result = await archive.find_movie(title)
    if not result:
        await query.message.reply(
            f"No public-domain / open-license copy of **{title}** found on Internet Archive."
        )
        return

    lines = [
        f"🌐 **{result['title']}** on Internet Archive",
        f"🔗 {result['archive_url']}",
        "",
        "**Direct links:**",
    ]
    for link in result["links"]:
        size = format_size(int(link["size"])) if link.get("size") else "?"
        lines.append(f"• [{link['name']}]({link['url']}) — {size}")

    await query.message.reply(
        "\n".join(lines),
        disable_web_page_preview=True,
    )


async def _similar_movies(client: Client, query: CallbackQuery, tmdb_id: int) -> None:
    await query.answer()
    details = await tmdb.get_movie_details(tmdb_id)
    similar = details.get("similar", {}).get("results", [])[:8]
    if not similar:
        await query.message.reply("No similar movies found.")
        return
    lines = ["🎥 **Similar Movies:**\n"]
    for m in similar:
        t = m.get("title", "?")
        y = (m.get("release_date") or "")[:4]
        r = round(m.get("vote_average", 0), 1)
        lines.append(f"• **{t}** ({y}) ⭐ {r}")
    await query.message.reply("\n".join(lines))


async def _trending_cb(client: Client, query: CallbackQuery) -> None:
    await query.answer()
    movies = await tmdb.get_trending()
    lines = ["🔥 **Trending This Week:**\n"]
    for i, m in enumerate(movies[:10], 1):
        lines.append(f"{i}. **{m.get('title', '?')}** ({(m.get('release_date') or '')[:4]}) ⭐ {round(m.get('vote_average', 0), 1)}")
    await query.message.edit_text("\n".join(lines), reply_markup=main_menu())


async def _recent_cb(client: Client, query: CallbackQuery) -> None:
    await query.answer()
    docs = await MovieRepository.get_recent(10)
    if not docs:
        await query.message.edit_text("No movies indexed yet.", reply_markup=main_menu())
        return
    lines = ["🆕 **Recently Added:**\n"]
    for m in docs:
        lines.append(f"• {build_simple_card(m)}")
    await query.message.edit_text("\n\n".join(lines), reply_markup=main_menu())


async def _genre_cb(client: Client, query: CallbackQuery, genre_id: int) -> None:
    await query.answer()
    genre_name = GENRES.get(genre_id, "Unknown")
    movies = await tmdb.get_by_genre(genre_id)
    if not movies:
        await query.message.edit_text(f"No {genre_name} movies found.", reply_markup=genres_keyboard())
        return
    lines = [f"🎭 **{genre_name} Movies:**\n"]
    for m in movies[:10]:
        t = m.get("title", "?")
        y = (m.get("release_date") or "")[:4]
        r = round(m.get("vote_average", 0), 1)
        lines.append(f"• **{t}** ({y}) ⭐ {r}")
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    await query.message.edit_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀ Back to Genres", callback_data="genres")]]),
    )


async def _user_list_cb(client: Client, query: CallbackQuery, list_type: str) -> None:
    await query.answer()
    uid = query.from_user.id
    user = await UserRepository.get(uid)
    if not user:
        await query.message.edit_text("Profile not found.")
        return

    if list_type == "watchlist":
        items = user.get("watchlist", [])
        header = "📋 **Your Watchlist**"
    elif list_type == "favorites":
        items = user.get("favorites", [])
        header = "❤️ **Your Favorites**"
    elif list_type == "history":
        items = list(reversed(user.get("search_history", [])[-20:]))
        header = "📜 **Recent Searches**"
    else:
        reqs = await RequestRepository.get_user_requests(uid)
        items = [f"{r.get('title', '?')} — _{r.get('status', '?')}_" for r in reqs]
        header = "📩 **Your Requests**"

    if not items:
        await query.message.edit_text(f"{header}\n\nNothing here yet.", reply_markup=main_menu())
        return

    text = header + "\n\n" + "\n".join(f"• {i}" for i in items)
    await query.message.edit_text(text, reply_markup=main_menu())
