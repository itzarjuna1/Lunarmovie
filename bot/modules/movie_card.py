from typing import Optional


def format_size(size_bytes: Optional[int]) -> str:
    if not size_bytes:
        return "N/A"
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def format_runtime(minutes: Optional[int]) -> str:
    if not minutes:
        return "N/A"
    h, m = divmod(minutes, 60)
    return f"{h}h {m}m" if h else f"{m}m"


def build_movie_card(meta: dict, db_movie: Optional[dict] = None) -> str:
    """
    Build a formatted Markdown movie card from TMDb metadata.
    `db_movie` is the indexed Telegram file document (optional).
    """
    title = meta.get("title", "Unknown")
    year = (meta.get("release_date") or "")[:4] or "N/A"
    rating = meta.get("rating", 0)
    votes = meta.get("vote_count", 0)
    overview = meta.get("overview") or "No overview available."
    genres = ", ".join(meta.get("genres", [])) or "N/A"
    runtime = format_runtime(meta.get("runtime"))
    directors = ", ".join(meta.get("directors", [])) or "N/A"
    cast = ", ".join(meta.get("cast", [])) or "N/A"
    tagline = meta.get("tagline", "")
    language = (meta.get("language") or "").upper() or "N/A"

    stars = _star_rating(rating)

    lines = [
        f"**{title}** ({year})",
    ]
    if tagline:
        lines.append(f"_\"{tagline}\"_")
    lines += [
        "",
        f"⭐ **{rating}/10** {stars} ({votes:,} votes)",
        f"🎭 **Genres:** {genres}",
        f"⏱ **Runtime:** {runtime}",
        f"🌐 **Language:** {language}",
        f"🎬 **Director:** {directors}",
        f"🎭 **Cast:** {cast}",
        "",
        f"📖 **Overview:**",
        f"{overview}",
    ]

    if db_movie:
        size_str = format_size(db_movie.get("size"))
        quality = db_movie.get("quality", "N/A")
        lines += [
            "",
            f"✅ **Available:** {quality} | {size_str}",
        ]

    return "\n".join(lines)


def build_simple_card(db_movie: dict) -> str:
    title = db_movie.get("movie_title", "Unknown")
    year = db_movie.get("year") or "N/A"
    quality = db_movie.get("quality") or "N/A"
    size = format_size(db_movie.get("size"))
    lang = db_movie.get("language") or "N/A"
    return f"**{title}** ({year})\n🎞 {quality} | 🌐 {lang} | 📦 {size}"


def _star_rating(rating: float) -> str:
    filled = round(rating / 2)
    return "★" * filled + "☆" * (5 - filled)
