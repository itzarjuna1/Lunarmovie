from typing import Any, Optional

import aiohttp

from bot.configs import config
from bot.utils.logger import log

_BASE = config.TMDB_BASE_URL
_IMG = config.TMDB_IMAGE_BASE_URL


class TMDbClient:
    def __init__(self) -> None:
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"Accept": "application/json"},
                timeout=aiohttp.ClientTimeout(total=10),
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def _request(self, path: str, params: dict[str, Any] | None = None) -> dict:
        session = await self._get_session()
        p = {"api_key": config.TMDB_API_KEY, **(params or {})}
        url = f"{_BASE}{path}"
        try:
            async with session.get(url, params=p) as resp:
                resp.raise_for_status()
                return await resp.json()
        except Exception as exc:
            log.warning("TMDb request failed %s: %s", path, exc)
            return {}

    # ── Public API ────────────────────────────────────────────────────────────

    def poster_url(self, path: Optional[str], size: str = "w500") -> Optional[str]:
        if not path:
            return None
        return f"{_IMG}/{size}{path}"

    async def search_movie(self, title: str, year: Optional[int] = None) -> Optional[dict]:
        params: dict[str, Any] = {"query": title, "include_adult": False}
        if year:
            params["year"] = year
        data = await self._request("/search/movie", params)
        results = data.get("results", [])
        return results[0] if results else None

    async def get_movie_details(self, tmdb_id: int) -> dict:
        return await self._request(
            f"/movie/{tmdb_id}",
            {"append_to_response": "credits,videos,similar,release_dates"},
        )

    async def get_trending(self, time_window: str = "week") -> list[dict]:
        data = await self._request(f"/trending/movie/{time_window}")
        return data.get("results", [])

    async def get_by_genre(self, genre_id: int, page: int = 1) -> list[dict]:
        data = await self._request(
            "/discover/movie",
            {"with_genres": genre_id, "sort_by": "popularity.desc", "page": page},
        )
        return data.get("results", [])

    async def enrich(self, title: str, year: Optional[int] = None) -> Optional[dict]:
        """Return a rich metadata dict ready to display."""
        basic = await self.search_movie(title, year)
        if not basic:
            return None
        details = await self.get_movie_details(basic["id"])
        if not details:
            return None

        credits = details.get("credits", {})
        cast = [
            m["name"] for m in credits.get("cast", [])[:5]
        ]
        directors = [
            m["name"]
            for m in credits.get("crew", [])
            if m.get("job") == "Director"
        ]

        trailer_key = None
        for v in details.get("videos", {}).get("results", []):
            if v.get("type") == "Trailer" and v.get("site") == "YouTube":
                trailer_key = v["key"]
                break

        similar = [
            m.get("title", "")
            for m in details.get("similar", {}).get("results", [])[:5]
        ]

        return {
            "tmdb_id": details.get("id"),
            "title": details.get("title"),
            "original_title": details.get("original_title"),
            "overview": details.get("overview"),
            "release_date": details.get("release_date"),
            "runtime": details.get("runtime"),
            "rating": round(details.get("vote_average", 0), 1),
            "vote_count": details.get("vote_count"),
            "genres": [g["name"] for g in details.get("genres", [])],
            "poster_url": self.poster_url(details.get("poster_path")),
            "backdrop_url": self.poster_url(details.get("backdrop_path"), "w1280"),
            "cast": cast,
            "directors": directors,
            "trailer_key": trailer_key,
            "similar": similar,
            "tagline": details.get("tagline"),
            "language": details.get("original_language"),
            "status": details.get("status"),
        }


tmdb = TMDbClient()
