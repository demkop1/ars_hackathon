"""Core data model & workflow-state types shared across the app.

These mirror the entities implied by the SVG screen-flow diagram:
an Event surfaced by the recommender, the user's Interests/Preferences,
and the WorkflowStage pipeline that gates Landing -> Interests -> Discover.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

# ---------------------------------------------------------------------------
# Workflow status vocabulary (used by the pipeline stepper & stage guards)
# ---------------------------------------------------------------------------

StageStatus = Literal[
    "not_started",
    "ready",
    "in_progress",
    "completed",
    "failed",
    "requires_attention",
]

Screen = Literal[
    "landing",
    "interests",
    "generating",
    "discover",
    "detail",
    "saved",
]


@dataclass(frozen=True)
class StageInfo:
    """One node of the pipeline stepper (Landing / Interests / Recommendations / Discover)."""

    id: str
    label: str
    caption: str
    status: StageStatus


# ---------------------------------------------------------------------------
# Domain entities
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Event:
    id: str
    title: str
    description: str
    tags: tuple[str, ...]
    location_name: str
    organizer_name: str
    free_of_charge: Optional[bool]
    suitable_for_children: Optional[bool]
    next_date: Optional[str]
    occurrence_count: int

    @staticmethod
    def from_dict(raw: dict) -> "Event":
        return Event(
            id=raw["id"],
            title=raw["title"],
            description=raw["description"],
            tags=tuple(raw.get("tags", [])),
            location_name=raw.get("location_name", "Location TBA"),
            organizer_name=raw.get("organizer_name", "Unknown organizer"),
            free_of_charge=raw.get("free_of_charge"),
            suitable_for_children=raw.get("suitable_for_children"),
            next_date=raw.get("next_date"),
            occurrence_count=int(raw.get("occurrence_count", 0)),
        )


@dataclass(frozen=True)
class TagInfo:
    name: str
    event_count: int


@dataclass
class Preferences:
    free_only: bool = False
    family_only: bool = False
    sort_mode: Literal["best_match", "soonest"] = "best_match"


@dataclass
class SwipeAction:
    event_id: str
    action: Literal["liked", "skipped"]
