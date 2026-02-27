"""Shared utilities."""

from datetime import datetime


def iso_utc(dt: datetime | None) -> str | None:
    """Format datetime as ISO 8601 with Z suffix (UTC) for correct frontend parsing."""
    if dt is None:
        return None
    s = dt.isoformat()
    if dt.tzinfo is None and "Z" not in s and "+" not in s:
        s += "Z"  # Naive UTC → explicit Z so browser parses as UTC
    return s
