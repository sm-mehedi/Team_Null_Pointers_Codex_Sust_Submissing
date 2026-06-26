from __future__ import annotations

from datetime import datetime, timezone


def parse_iso8601(value: str) -> datetime | None:
    try:
        cleaned = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(cleaned)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None
