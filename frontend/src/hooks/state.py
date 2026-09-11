"""Central session-state management.

Streamlit re-runs the whole script on every interaction, so this module is
the single source of truth for "where is the user in the workflow" and
"what have they done so far". Components/features read and mutate it
through the `AppState` proxy instead of touching `st.session_state` keys
directly, so the key names only live in one place.
"""
from __future__ import annotations

from typing import Optional

import streamlit as st

from src.types.models import Screen, StageInfo, StageStatus

MIN_TAGS_REQUIRED = 3

_DEFAULTS = {
    "screen": "landing",
    "selected_tags": [],
    "pref_highlights_only": False,
    "pref_sort_mode": "best_match",  # best_match | soonest
    # Snapshots of the above, taken the moment "Continue" is clicked on the
    # Interests screen. Streamlit clears a widget-bound session_state value
    # once that widget stops being rendered (i.e. as soon as we navigate away
    # from Interests), so anything read *after* that point -- generation,
    # the deck, sidebar summaries -- must read these stable copies instead of
    # the live `selected_tags`/`pref_*` widget keys.
    "confirmed_tags": [],
    "confirmed_highlights_only": False,
    "confirmed_sort_mode": "best_match",
    "gen_status": "not_started",  # not_started | in_progress | completed | failed
    "gen_error": None,
    "deck": [],  # ranked list[event_id]
    "match_counts": {},  # event_id -> matched tag count, from the last generation
    "deck_index": 0,
    "liked_ids": [],
    "skipped_ids": [],
    "history": [],  # list[{"event_id", "action"}] for Undo
    "detail_event_id": None,
    "detail_from": "discover",
    "sim_fail_mode": "off",  # off | always_fail | random -- no UI to change this anymore, kept for generate_recommendations()'s signature
    "sim_delay": 0.0,
    "show_overview": False,
}


class AppState:
    """Thin attribute-style proxy over `st.session_state`."""

    def __getattr__(self, name):
        try:
            return st.session_state[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, value):
        st.session_state[name] = value


def init_state() -> AppState:
    for key, default in _DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default
    return AppState()


def get_state() -> AppState:
    return AppState()


def go_to(screen: Screen) -> None:
    st.session_state["screen"] = screen
    st.rerun()


def reset_workflow() -> None:
    """Request a full reset. Several of the keys involved (selected_tags,
    pref_*, sim_*, show_overview) are bound to widgets that render earlier
    in the same script pass than this button, and Streamlit forbids writing
    to a session_state key after its widget has already been instantiated
    this run. So we only flag the request here; `apply_pending_reset()` --
    called at the very top of app.py, before any widget exists yet -- does
    the actual reassignment on the next run."""
    st.session_state["_reset_requested"] = True
    st.rerun()


def apply_pending_reset() -> None:
    if st.session_state.pop("_reset_requested", False):
        for key, default in _DEFAULTS.items():
            st.session_state[key] = default


# ---------------------------------------------------------------------------
# Swipe deck mutations
# ---------------------------------------------------------------------------


def current_event_id(ss: AppState) -> Optional[str]:
    if ss.deck and ss.deck_index < len(ss.deck):
        return ss.deck[ss.deck_index]
    return None


def record_swipe(ss: AppState, event_id: str, action: str) -> None:
    if action == "liked":
        if event_id not in ss.liked_ids:
            ss.liked_ids = [event_id, *ss.liked_ids]
        ss.skipped_ids = [i for i in ss.skipped_ids if i != event_id]
    else:
        if event_id not in ss.skipped_ids:
            ss.skipped_ids = [*ss.skipped_ids, event_id]
        ss.liked_ids = [i for i in ss.liked_ids if i != event_id]
    ss.history = [*ss.history, {"event_id": event_id, "action": action}]
    ss.deck_index = ss.deck_index + 1


def undo_last_swipe(ss: AppState) -> None:
    if not ss.history:
        return
    history = list(ss.history)
    last = history.pop()
    ss.history = history
    ss.deck_index = max(0, ss.deck_index - 1)
    if last["action"] == "liked":
        ss.liked_ids = [i for i in ss.liked_ids if i != last["event_id"]]
    else:
        ss.skipped_ids = [i for i in ss.skipped_ids if i != last["event_id"]]


def remove_saved(ss: AppState, event_id: str) -> None:
    ss.liked_ids = [i for i in ss.liked_ids if i != event_id]


def open_detail(ss: AppState, event_id: str, from_screen: Screen) -> None:
    ss.detail_event_id = event_id
    ss.detail_from = from_screen
    go_to("detail")


def close_detail(ss: AppState) -> None:
    target = ss.detail_from or "discover"
    ss.detail_event_id = None
    go_to(target)


# ---------------------------------------------------------------------------
# Pipeline stepper status derivation
# ---------------------------------------------------------------------------


def compute_stage_statuses(ss: AppState) -> list[StageInfo]:
    landing_status: StageStatus = "completed" if ss.screen != "landing" else "ready"

    if ss.screen == "landing":
        interests_status: StageStatus = "not_started"
    elif ss.screen == "interests":
        interests_status = "requires_attention" if len(ss.selected_tags) < MIN_TAGS_REQUIRED else "in_progress"
    else:
        interests_status = "completed"

    if ss.screen in ("landing", "interests"):
        rec_status: StageStatus = "not_started"
    elif ss.screen == "generating":
        rec_status = "failed" if ss.gen_status == "failed" else "in_progress"
    else:
        rec_status = "completed" if ss.gen_status == "completed" else "not_started"

    if rec_status != "completed":
        discover_status: StageStatus = "not_started"
    elif ss.deck and ss.deck_index >= len(ss.deck):
        discover_status = "completed"
    elif ss.screen in ("discover", "detail", "saved"):
        discover_status = "in_progress"
    else:
        discover_status = "ready"

    return [
        StageInfo("landing", "Landing", "App intro & get started", landing_status),
        StageInfo("interests", "Interests", "Pick tags & preferences", interests_status),
        StageInfo("recommendations", "Recommendations", "Curating your deck", rec_status),
        StageInfo("discover", "Discover", "Swipe through events", discover_status),
    ]
