"""In-memory data store, loaded once at startup from data/prepared_cards.json.

That file (repo root, not a copy under this package) is the real, current
dataset -- 383 Ars Electronica Festival 2026 event cards. Loaded once into
memory since it's small and static; swap `_load()` for a real data source
later without touching anything downstream, which only depends on
`get_events()` / `get_tags()` returning plain dicts shaped like
`EventOut` / `TagOut`.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Optional

_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "prepared_cards.json"


def _load() -> list[dict]:
    with open(_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


_EVENTS: list[dict] = _load()
_EVENTS_BY_ID: dict[str, dict] = {e["id"]: e for e in _EVENTS}
_TAGS: list[dict] = [
    {"name": name, "event_count": count}
    for name, count in Counter(e["category"] for e in _EVENTS).most_common()
]


def get_events() -> list[dict]:
    return _EVENTS


def get_event(event_id: str) -> Optional[dict]:
    return _EVENTS_BY_ID.get(event_id)


def get_tags() -> list[dict]:
    return _TAGS
