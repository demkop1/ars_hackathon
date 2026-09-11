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
class EventLocation:
    venue: str
    area: str
    lat: Optional[float]
    lng: Optional[float]
    services: Optional[str]

    @staticmethod
    def from_dict(raw: dict) -> "EventLocation":
        return EventLocation(
            venue=raw.get("venue") or "Venue TBA",
            area=raw.get("area") or "",
            lat=raw.get("lat"),
            lng=raw.get("lng"),
            services=raw.get("services"),
        )


@dataclass(frozen=True)
class Event:
    """Mirrors a record in data/prepared_cards.json -- one card per festival event."""

    id: str
    title: str
    category: str
    highlight: bool
    time: str  # already a display-ready string, e.g. "9. September 2026 15:15 (MESZ) -> 16:15"
    location: EventLocation
    preview_text: str
    full_desc: str
    embedding_input: str

    @staticmethod
    def from_dict(raw: dict) -> "Event":
        return Event(
            id=raw["id"],
            title=raw["title"],
            category=raw.get("category") or "Uncategorized",
            highlight=bool(raw.get("highlight", False)),
            time=raw.get("time") or "Date to be announced",
            location=EventLocation.from_dict(raw.get("location") or {}),
            preview_text=raw.get("preview_text") or "",
            full_desc=raw.get("full_desc") or "",
            embedding_input=raw.get("embedding_input") or "",
        )


@dataclass(frozen=True)
class TagInfo:
    """A distinct `category` value from prepared_cards.json, with how many cards have it."""

    name: str
    event_count: int


@dataclass
class Preferences:
    highlights_only: bool = False
    sort_mode: Literal["best_match", "soonest"] = "best_match"


@dataclass
class SwipeAction:
    event_id: str
    action: Literal["liked", "skipped"]
