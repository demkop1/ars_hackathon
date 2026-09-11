"""Static mock-data loaders.

The events/tags bundled here are a real, trimmed snapshot of the City of
Linz's public events feed (`Linztermine.json`, see ../../../data at the repo
root) frozen into JSON so this frontend has no live dependency. Swap these
loaders for real API calls once a backend exists -- everything downstream
(ranking, session state, UI) already consumes plain `Event`/`TagInfo`
objects and does not care where they came from.
"""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from src.types.models import Event, TagInfo

_DATA_DIR = Path(__file__).parent


@st.cache_data(show_spinner=False)
def load_events() -> list[Event]:
    with open(_DATA_DIR / "events.json", encoding="utf-8") as f:
        raw = json.load(f)
    return [Event.from_dict(r) for r in raw]


@st.cache_data(show_spinner=False)
def load_tags() -> list[TagInfo]:
    with open(_DATA_DIR / "tags.json", encoding="utf-8") as f:
        raw = json.load(f)
    return [TagInfo(name=r["name"], event_count=r["event_count"]) for r in raw]


def events_by_id() -> dict[str, Event]:
    return {e.id: e for e in load_events()}
