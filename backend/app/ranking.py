"""Recommendation ranking.

prepared_cards.json has one `category` per card (not a list of tags) and no
price/child-friendly flags -- only a `highlight` bool -- so scoring is a
simple category-membership check and filtering is a single toggle, not the
overlap-count + two-filter logic an older, differently-shaped dataset used.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from app.models import RecommendationRequest

_MONTHS_DE = {
    "Januar": 1, "Februar": 2, "März": 3, "April": 4, "Mai": 5, "Juni": 6,
    "Juli": 7, "August": 8, "September": 9, "Oktober": 10, "November": 11, "Dezember": 12,
}
_TIME_RE = re.compile(r"(\d+)\.\s+(\w+)\s+(\d{4})\s+(\d{1,2}):(\d{2})")


def _parse_sort_key(time_str: Optional[str]) -> str:
    """'9. September 2026 15:15 (MESZ) -> 16:15' -> '20260909 1515' (sortable).
    Falls back to a key that sorts last for anything unparseable."""
    if not time_str:
        return "99999999 9999"
    match = _TIME_RE.match(time_str)
    if not match:
        return "99999999 9999"
    day, month_name, year, hour, minute = match.groups()
    month = _MONTHS_DE.get(month_name, 0)
    try:
        datetime(int(year), month, int(day), int(hour), int(minute))
    except ValueError:
        return "99999999 9999"
    return f"{int(year):04d}{month:02d}{int(day):02d} {int(hour):02d}{int(minute):02d}"


def _score(event: dict, selected_categories: set[str]) -> int:
    return 1 if event.get("category") in selected_categories else 0


def generate_recommendations(
    events: list[dict],
    request: RecommendationRequest,
) -> tuple[list[str], dict[str, int]]:
    selected_categories = set(request.tags)

    candidates = list(events)
    if request.highlights_only:
        candidates = [e for e in candidates if e.get("highlight") is True]

    scored = [(e, _score(e, selected_categories)) for e in candidates]
    scored = [(e, s) for e, s in scored if s > 0] or [(e, 0) for e in candidates]

    if request.sort_mode == "soonest":
        scored.sort(key=lambda pair: (_parse_sort_key(pair[0].get("time")), -pair[1]))
    else:
        scored.sort(key=lambda pair: (-pair[1], _parse_sort_key(pair[0].get("time"))))

    ranked_event_ids = [e["id"] for e, _ in scored]
    matched_tag_count = {e["id"]: s for e, s in scored}
    return ranked_event_ids, matched_tag_count
