import re
from dataclasses import dataclass
from typing import Optional


_QUALITY_RE = re.compile(
    r"\b(4K|2160p|1080p|720p|480p|360p|HDR|HDRip|BluRay|BRRip|WEBRip|WEB-DL|HDTV|DVDRip|DVD)\b",
    re.IGNORECASE,
)
_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
_CODEC_RE = re.compile(
    r"\b(x264|x265|HEVC|AVC|H\.?264|H\.?265|XviD|DivX|AV1)\b", re.IGNORECASE
)
_LANG_RE = re.compile(
    r"\b(Hindi|English|Tamil|Telugu|Malayalam|Kannada|Punjabi|Bengali|"
    r"Marathi|Dual\.Audio|Multi\.Audio|Dubbed|ENG|HIN|TAM|TEL)\b",
    re.IGNORECASE,
)
_CLEAN_RE = re.compile(r"[\[\](){}]")
_MULTI_SPACE = re.compile(r"\s{2,}")


@dataclass
class ParsedFile:
    title: str
    year: Optional[int]
    quality: Optional[str]
    codec: Optional[str]
    language: Optional[str]
    raw: str


def parse_filename(filename: str) -> ParsedFile:
    name = filename
    # Strip extension
    name = re.sub(r"\.[a-zA-Z0-9]{2,4}$", "", name)
    # Replace separators
    name = name.replace(".", " ").replace("_", " ").replace("-", " ")
    name = _CLEAN_RE.sub(" ", name)

    quality_m = _QUALITY_RE.search(name)
    quality = quality_m.group(0).upper() if quality_m else None
    if quality_m:
        quality = _normalise_quality(quality)

    year_m = _YEAR_RE.search(name)
    year = int(year_m.group(0)) if year_m else None

    codec_m = _CODEC_RE.search(name)
    codec = codec_m.group(0).upper() if codec_m else None

    lang_m = _LANG_RE.search(name)
    language = lang_m.group(0).title() if lang_m else None

    # Build title: everything before the first tag
    cut = len(name)
    for m in [quality_m, year_m, codec_m, lang_m]:
        if m and m.start() < cut:
            cut = m.start()

    title = name[:cut].strip()
    title = _MULTI_SPACE.sub(" ", title).title()

    return ParsedFile(
        title=title or filename,
        year=year,
        quality=quality,
        codec=codec,
        language=language,
        raw=filename,
    )


def _normalise_quality(raw: str) -> str:
    mapping = {
        "2160P": "2160p",
        "4K": "2160p",
        "1080P": "1080p",
        "720P": "720p",
        "480P": "480p",
        "360P": "360p",
    }
    return mapping.get(raw.upper(), raw)
