"""Recommendation ranking.

Ported 1:1 from `frontend/src/utils/mock_backend.py` so switching the
frontend from its local simulation to this real endpoint changes nothing
about the ranking behavior a user sees. The frontend's artificial
delay/failure simulation (for exercising its own loading/error states) is
deliberately *not* reproduced here -- that's a frontend-testing concern,
not something a real backend should fake.
"""
from __future__ import annotations

from app.models import RecommendationRequest


def _score(event: dict, selected_tags: set[str]) -> int:
    return len(set(event.get("tags", [])) & selected_tags)


def generate_recommendations(
    events: list[dict],
    request: RecommendationRequest,
) -> tuple[list[str], dict[str, int]]:
    selected_tags = set(request.tags)

    candidates = list(events)
    if request.free_only:
        candidates = [e for e in candidates if e.get("free_of_charge") is True]
    if request.family_only:
        candidates = [e for e in candidates if e.get("suitable_for_children") is True]

    scored = [(e, _score(e, selected_tags)) for e in candidates]
    scored = [(e, s) for e, s in scored if s > 0] or [(e, 0) for e in candidates]

    if request.sort_mode == "soonest":
        scored.sort(key=lambda pair: (pair[0].get("next_date") or "9999", -pair[1]))
    else:
        scored.sort(key=lambda pair: (-pair[1], pair[0].get("next_date") or "9999"))

    ranked_event_ids = [e["id"] for e, _ in scored]
    matched_tag_count = {e["id"]: s for e, s in scored}
    return ranked_event_ids, matched_tag_count
