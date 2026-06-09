from pyrogram import Client
from pyrogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InlineQueryResultPhoto,
    InputTextMessageContent,
)

from bot.modules import build_movie_card, movie_actions
from bot.services import search_engine, tmdb
from bot.utils.decorators import log_errors


@Client.on_inline_query()
@log_errors
async def inline_handler(client: Client, query: InlineQuery) -> None:
    q = (query.query or "").strip()
    if not q:
        await query.answer(
            results=[],
            switch_pm_text="give a search query as movie name ",
            switch_pm_parameter="start",
            cache_time=0,
        )
        return

    results_db, total = await search_engine.search(q, page=1, page_size=8)

    articles = []
    for doc in results_db:
        title = doc.get("movie_title", q)
        year = doc.get("year")
        quality = doc.get("quality", "")
        fuid = doc.get("file_unique_id", "")

        meta = await tmdb.enrich(title, year)

        if meta and meta.get("poster_url"):
            card = build_movie_card(meta, doc)
            articles.append(
                InlineQueryResultPhoto(
                    photo_url=meta["poster_url"],
                    thumb_url=meta.get("poster_url", ""),
                    title=f"{title} ({year or '?'}) {quality}".strip(),
                    description=(meta.get("overview") or "")[:100],
                    caption=card,
                )
            )
        else:
            articles.append(
                InlineQueryResultArticle(
                    title=f"{title} ({year or '?'}) {quality}".strip(),
                    description=f"Quality: {quality or 'N/A'}",
                    input_message_content=InputTextMessageContent(
                        f"**{title}** ({year or 'N/A'}) — {quality or 'N/A'}"
                    ),
                )
            )

    if not articles:
        articles.append(
            InlineQueryResultArticle(
                title="No results found",
                description=f"No indexed movie matching '{q}'",
                input_message_content=InputTextMessageContent(
                    f"No results for **{q}**. Try the bot in DM to request this movie."
                ),
            )
        )

    await query.answer(results=articles, cache_time=10)
#chache time refreshed 
