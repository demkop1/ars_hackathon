from __future__ import annotations

from datetime import datetime


def format_event_date(iso_str: str | None) -> str:
    """'2026-09-12T18:00:00+02:00' -> 'Sat, 12 Sep · 18:00'."""
    if not iso_str:
        return "Date to be announced"
    try:
        dt = datetime.fromisoformat(iso_str)
    except ValueError:
        return iso_str
    return dt.strftime("%a, %d %b · %H:%M")


def format_relative_hint(occurrence_count: int) -> str:
    if occurrence_count <= 0:
        return "One-time event"
    if occurrence_count == 1:
        return "1 upcoming date"
    return f"{occurrence_count} upcoming dates"
