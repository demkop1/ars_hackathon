from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app import store
from app.models import EventOut

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[EventOut])
def list_events() -> list[dict]:
    return store.get_events()


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: str) -> dict:
    event = store.get_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail=f"No event with id '{event_id}'")
    return event
