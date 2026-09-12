from __future__ import annotations

import streamlit as st

from src.components.empty_state import render_empty_state
from src.data.loader import load_events
from src.hooks.state import AppState, go_to
from src.types.models import Preferences
from src.utils.mock_backend import RecommendationError, generate_recommendations


def render(ss: AppState) -> None:
    # Two-step (not_started -> in_progress) so the sidebar stepper has a chance
    # to render the "in progress" badge before the (simulated) blocking call runs.
    if ss.gen_status == "not_started":
        ss.gen_status = "in_progress"
        st.rerun()

    elif ss.gen_status == "in_progress":
        selected = list(ss.confirmed_tags or [])
        prefs = Preferences(
            highlights_only=ss.confirmed_highlights_only,
            sort_mode=ss.confirmed_sort_mode,
        )
        spinner_text = (
            f"Matching events to your {len(selected)} interests…"
            if selected
            else "Curating your deck…"
        )
        with st.spinner(spinner_text):
            try:
                result = generate_recommendations(
                    load_events(),
                    set(selected),
                    prefs,
                    interests_text=ss.confirmed_interests_text,
                    fail_mode=ss.sim_fail_mode,
                    delay_seconds=ss.sim_delay,
                )
            except RecommendationError as exc:
                ss.gen_status = "failed"
                ss.gen_error = str(exc)
                st.rerun()
            else:
                ss.deck = result.ranked_event_ids
                ss.match_counts = result.matched_tag_count
                ss.deck_index = 0
                ss.gen_status = "completed"
                go_to("discover")

    elif ss.gen_status == "failed":
        retry = render_empty_state(
            icon="⚠️",
            title="We couldn't generate your recommendations",
            message=ss.gen_error or "Something went wrong while curating your deck.",
            action_label="Retry",
            key="retry_generation",
        )
        if retry:
            ss.gen_status = "not_started"
            st.rerun()
        _, mid, _ = st.columns([1, 1, 1])
        with mid:
            if st.button("← Adjust interests instead", use_container_width=True):
                go_to("interests")

    else:  # completed but user navigated back here somehow -- offer a clean way forward
        st.success("Your deck is ready.")
        if st.button("Go to Discover →", type="primary"):
            go_to("discover")
