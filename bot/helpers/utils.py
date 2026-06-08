def human_size(size_bytes: int | None) -> str:
    if not size_bytes:
        return "N/A"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:3.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def truncate(text: str, length: int = 200, suffix: str = "…") -> str:
    if len(text) <= length:
        return text
    return text[:length].rstrip() + suffix
