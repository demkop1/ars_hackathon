"""Data loaders backed by the FastAPI service.

Fetches events and tags from the backend HTTP API, parsing them into
plain Event and TagInfo objects. Streamlit caching is set with a TTL so
updates from the backend are periodically reflected without requiring a restart.
"""
from __future__ import annotations

import os
import requests
import streamlit as st

from src.types.models import Event, TagInfo

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


@st.cache_data(show_spinner=False, ttl=600)
def load_events() -> list[Event]:
    try:
        response = requests.get(f"{BACKEND_URL}/events", timeout=5)
        response.raise_for_status()
        raw = response.json()
        return [Event.from_dict(r) for r in raw]
    except requests.RequestException as exc:
        st.error(f"Failed to load events from backend ({BACKEND_URL}): {exc}")
        return []


@st.cache_data(show_spinner=False, ttl=600)
def load_tags() -> list[TagInfo]:
    try:
        response = requests.get(f"{BACKEND_URL}/tags", timeout=5)
        response.raise_for_status()
        raw = response.json()
        return [TagInfo(name=r["name"], event_count=r["event_count"]) for r in raw]
    except requests.RequestException as exc:
        st.error(f"Failed to load tags from backend ({BACKEND_URL}): {exc}")
        return []


def events_by_id() -> dict[str, Event]:
    return {e.id: e for e in load_events()}