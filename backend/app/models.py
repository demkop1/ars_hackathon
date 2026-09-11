"""Pydantic request/response schemas.

Field names deliberately mirror `frontend/src/types/models.py` (Event,
EventLocation, TagInfo, Preferences) so the frontend's existing
`Event.from_dict()` construction keeps working unchanged. Both sides mirror
the actual shape of data/prepared_cards.json, not an idealized one --
there's no organizer/price/child-friendly data in that file, so those
fields don't exist here either.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel


class LocationOut(BaseModel):
    venue: str
    area: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    services: Optional[str] = None


class EventOut(BaseModel):
    id: str
    title: str
    category: str
    highlight: bool
    time: str
    location: LocationOut
    preview_text: str
    full_desc: str
    embedding_input: str


class TagOut(BaseModel):
    name: str
    event_count: int


class RecommendationRequest(BaseModel):
    tags: list[str]  # selected `category` values
    highlights_only: bool = False
    sort_mode: Literal["best_match", "soonest"] = "best_match"


class RecommendationResponse(BaseModel):
    ranked_event_ids: list[str]
    matched_tag_count: dict[str, int]
