"""Backend HTTP client for recommendations.

Delegates recommendation scoring to the FastAPI service (`POST /recommendations`).
Catches connection and timeout errors and re-raises them as `RecommendationError`
to preserve the existing retry and failure UI flow.
"""
from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass, field
from typing import Literal

import requests

from src.types.models import Event, Preferences

FailMode = Literal["off", "always_fail", "random"]
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


class RecommendationError(RuntimeError):
    """Raised when the recommendation service fails or is unreachable."""


@dataclass(frozen=True)
class RecommendationResult:
    ranked_event_ids: list[str]
    matched_tag_count: dict[str, int]
    interests_valid: bool = True
    match_explanations: dict[str, str] = field(default_factory=dict)  # event_id -> "why this suits you" sentence


def generate_recommendations(
    events: list[Event],
    selected_tags: set[str],
    prefs: Preferences,
    *,
    interests_text: str = "",
    fail_mode: FailMode = "off",
    delay_seconds: float = 0.0,
) -> RecommendationResult:
    """Send recommendation request to the FastAPI backend service."""
    if delay_seconds > 0:
        time.sleep(delay_seconds)

    # Preserve the sidebar's simulated failure toggle for demo / testing
    if fail_mode == "always_fail" or (fail_mode == "random" and random.random() < 0.5):
        raise RecommendationError(
            "The recommendation service timed out while scoring your interests. "
            "(Simulated failure -- toggle 'Simulate backend failure' off in the sidebar to stop seeing this.)"
        )

    payload = {
        "tags": list(selected_tags),
        "interests_text": interests_text,
        "highlights_only": prefs.highlights_only,
        "sort_mode": prefs.sort_mode,
    }

    try:
        response = requests.post(
            f"{BACKEND_URL}/recommendations",
            json=payload,
            # /recommendations now makes up to 3 sequential LLM calls server-side
            # (validate interests, rewrite query, batch-explain matches) -- 8s was
            # fine for the old single-call version but is tight enough now to
            # flake on ordinary latency variance, not just genuine backend hangs.
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return RecommendationResult(
            ranked_event_ids=data["ranked_event_ids"],
            matched_tag_count=data["matched_tag_count"],
            interests_valid=data.get("interests_valid", True),
            match_explanations=data.get("match_explanations", {}),
        )
    except requests.Timeout as exc:
        raise RecommendationError(
            "The recommendation service timed out. Please verify the backend is responsive."
        ) from exc
    except requests.RequestException as exc:
        raise RecommendationError(
            f"Could not reach recommendation backend at {BACKEND_URL}: {exc}"
        ) from exc
