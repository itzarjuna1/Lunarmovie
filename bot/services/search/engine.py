from typing import Any

from bot.database.repositories.movies import MovieRepository
from bot.utils.logger import log


class SearchEngine:
    @staticmethod
    async def search(
        query: str,
        page: int = 1,
        page_size: int = 10,
        quality: str | None = None,
        language: str | None = None,
        year: int | None = None,
    ) -> tuple[list[dict], int]:
        filters: dict[str, Any] = {}
        if quality:
            filters["quality"] = {"$regex": quality, "$options": "i"}
        if language:
            filters["language"] = {"$regex": language, "$options": "i"}
        if year:
            filters["year"] = year

        results, total = await MovieRepository.search(
            query, page=page, page_size=page_size, filters=filters
        )
        log.debug("Search '%s' page=%d → %d/%d results", query, page, len(results), total)
        return results, total

    @staticmethod
    async def suggestions(query: str, limit: int = 5) -> list[str]:
        """Return distinct movie title suggestions for a partial query."""
        import re
        from bot.database.client import get_db

        escaped = re.escape(query)
        coll = get_db()["movies"]
        docs = (
            await coll.find(
                {"movie_title": {"$regex": f"^{escaped}", "$options": "i"}},
                {"movie_title": 1},
            )
            .limit(limit)
            .to_list(length=limit)
        )
        seen: set[str] = set()
        result: list[str] = []
        for d in docs:
            t = d.get("movie_title", "")
            if t and t not in seen:
                seen.add(t)
                result.append(t)
        return result


search_engine = SearchEngine()
