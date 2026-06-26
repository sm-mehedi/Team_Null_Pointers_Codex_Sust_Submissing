from __future__ import annotations

import re
import unicodedata


_SPACE_RE = re.compile(r"\s+")


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKC", value)
    normalized = normalized.replace("\u200b", "")
    normalized = _SPACE_RE.sub(" ", normalized)
    return normalized.strip().casefold()


def normalized_lower(value: str | None) -> str:
    return normalize_text(value).casefold()


def contains_any(text: str, needles: list[str] | tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def digits_only(value: str | None) -> str:
    return "".join(ch for ch in normalize_text(value) if ch.isdigit())
