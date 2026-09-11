"""Simulated backend calls.

There is no real API yet. This module is the single place that pretends to
be one: it takes a moment (configurable), can be made to fail (configurable),
and returns a ranked list of event ids. Replace the body of
`generate_recommendations` with a real HTTP call when a backend exists --
callers only depend on its signature, not its implementation.
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Literal

from src.types.models import Event, Preferences

FailMode = Literal["off", "always_fail", "random"]


class RecommendationError(RuntimeError):
    """Raised when the (simulated) recommendation service fails."""


@dataclass(frozen=True)
class RecommendationResult:
    ranked_event_ids: list[str]
    matched_tag_count: dict[str, int]


def _score(event: Event, selected_tags: set[str]) -> int:
    return len(set(event.tags) & selected_tags)


def generate_recommendations(
    events: list[Event],
    selected_tags: set[str],
    prefs: Preferences,
    *,
    fail_mode: FailMode = "off",
    delay_seconds: float = 1.2,
) -> RecommendationResult:
    """Simulate an async ranking call against the (future) recommender backend."""
    if delay_seconds > 0:
        time.sleep(delay_seconds)

    if fail_mode == "always_fail" or (fail_mode == "random" and random.random() < 0.5):
        raise RecommendationError(
            "The recommendation service timed out while scoring your interests. "
            "(Simulated failure -- toggle 'Simulate backend failure' off in the sidebar to stop seeing this.)"
        )

    candidates = list(events)
    if prefs.free_only:
        candidates = [e for e in candidates if e.free_of_charge is True]
    if prefs.family_only:
        candidates = [e for e in candidates if e.suitable_for_children is True]

    scored = [(e, _score(e, selected_tags)) for e in candidates]
    scored = [(e, s) for e, s in scored if s > 0] or [(e, 0) for e in candidates]

    if prefs.sort_mode == "soonest":
        scored.sort(key=lambda pair: (pair[0].next_date or "9999", -pair[1]))
    else:
        scored.sort(key=lambda pair: (-pair[1], pair[0].next_date or "9999"))

    matched_tag_count = {e.id: s for e, s in scored}
    return RecommendationResult(
        ranked_event_ids=[e.id for e, _ in scored],
        matched_tag_count=matched_tag_count,
    )
