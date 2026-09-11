"""Pydantic request/response schemas.

Field names deliberately mirror `frontend/src/types/models.py` (Event,
TagInfo, Preferences) so the frontend's existing `Event.from_dict()` /
`TagInfo(...)` construction keeps working unchanged once it's pointed at
this API instead of its bundled JSON.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel


class EventOut(BaseModel):
    id: str
    title: str
    description: str
    tags: list[str]
    location_name: str
    organizer_name: str
    free_of_charge: Optional[bool]
    suitable_for_children: Optional[bool]
    next_date: Optional[str]
    occurrence_count: int


class TagOut(BaseModel):
    name: str
    event_count: int


class RecommendationRequest(BaseModel):
    tags: list[str]
    free_only: bool = False
    family_only: bool = False
    sort_mode: Literal["best_match", "soonest"] = "best_match"


class RecommendationResponse(BaseModel):
    ranked_event_ids: list[str]
    matched_tag_count: dict[str, int]
