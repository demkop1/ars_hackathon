"""In-memory data store.

The dataset is small and mostly static (a trimmed snapshot of Linz events),
so it's loaded once into memory at startup rather than through a database.
Swap `_load()` for a real data source later (the full `data/Linztermine.json`
or `data/notion_export.json` at the repo root, or a DB) -- everything else
in this service only depends on `get_events()` / `get_tags()` returning
plain dicts shaped like `EventOut` / `TagOut`.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

_DATA_DIR = Path(__file__).parent / "data"


def _load(filename: str) -> list[dict]:
    with open(_DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


_EVENTS: list[dict] = _load("events.json")
_TAGS: list[dict] = _load("tags.json")
_EVENTS_BY_ID: dict[str, dict] = {e["id"]: e for e in _EVENTS}


def get_events() -> list[dict]:
    return _EVENTS


def get_event(event_id: str) -> Optional[dict]:
    return _EVENTS_BY_ID.get(event_id)


def get_tags() -> list[dict]:
    return _TAGS
