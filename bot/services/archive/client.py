from typing import Optional

import aiohttp

from bot.utils.logger import log

_SEARCH_URL = "https://archive.org/advancedsearch.php"
_DETAILS_URL = "https://archive.org/metadata"
_DOWNLOAD_BASE = "https://archive.org/download"


class ArchiveClient:
    def __init__(self) -> None:
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=15)
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def search(self, title: str, max_results: int = 5) -> list[dict]:
        """Search Internet Archive for open-license / public-domain movies."""
        session = await self._get_session()
        params = {
            "q": f'title:"{title}" AND mediatype:movies AND licenseurl:("http://creativecommons.org/*" OR "https://creativecommons.org/*" OR "http://www.archive.org/details/*")',
            "fl[]": ["identifier", "title", "year", "creator", "description", "avg_rating"],
            "rows": max_results,
            "page": 1,
            "output": "json",
        }
        try:
            async with session.get(_SEARCH_URL, params=params) as resp:
                resp.raise_for_status()
                data = await resp.json(content_type=None)
                return data.get("response", {}).get("docs", [])
        except Exception as exc:
            log.warning("Internet Archive search failed for '%s': %s", title, exc)
            return []

    async def get_download_links(self, identifier: str) -> list[dict]:
        """Return a list of video file download links for an Archive.org item."""
        session = await self._get_session()
        url = f"{_DETAILS_URL}/{identifier}"
        try:
            async with session.get(url) as resp:
                resp.raise_for_status()
                data = await resp.json(content_type=None)
        except Exception as exc:
            log.warning("Archive.org metadata failed for %s: %s", identifier, exc)
            return []

        video_exts = {".mp4", ".mkv", ".avi", ".ogv", ".webm"}
        links = []
        for file in data.get("files", []):
            name: str = file.get("name", "")
            if any(name.endswith(ext) for ext in video_exts):
                links.append(
                    {
                        "name": name,
                        "url": f"{_DOWNLOAD_BASE}/{identifier}/{name}",
                        "size": file.get("size"),
                        "format": file.get("format", ""),
                    }
                )
        return links

    async def find_movie(self, title: str) -> Optional[dict]:
        """High-level: return the first matching item with its download links."""
        results = await self.search(title, max_results=3)
        for item in results:
            identifier = item.get("identifier")
            if not identifier:
                continue
            links = await self.get_download_links(identifier)
            if links:
                return {
                    "identifier": identifier,
                    "title": item.get("title", title),
                    "year": item.get("year"),
                    "description": item.get("description", ""),
                    "archive_url": f"https://archive.org/details/{identifier}",
                    "links": links[:3],
                }
        return None


archive = ArchiveClient()
