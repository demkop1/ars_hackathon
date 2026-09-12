from __future__ import annotations

import streamlit as st

from src.components.event_card import render_event_card
from src.data.loader import events_by_id
from src.hooks.state import AppState, close_detail, record_swipe, remove_saved


def render(ss: AppState) -> None:
    event_id = ss.detail_event_id
    events = events_by_id()
    if not event_id or event_id not in events:
        st.warning("This event is no longer available.")
        if st.button("← Back"):
            close_detail(ss)
        return

    event = events[event_id]
    liked = event_id in ss.liked_ids
    skipped = event_id in ss.skipped_ids

    if st.button("← Back", key="detail_back_top"):
        close_detail(ss)

    render_event_card(
        event,
        variant="detail",
        match_count=ss.match_counts.get(event_id),
        explanation=ss.match_explanations.get(event_id),
    )

    st.write("")
    if liked:
        st.success("You've saved this event.", icon="❤️")
        if st.button("💔 Remove from saved", use_container_width=True):
            remove_saved(ss, event_id)
            close_detail(ss)
    elif skipped:
        st.info("You skipped this event.", icon="✖️")
        if st.button("❤ Save it instead", use_container_width=True, type="primary"):
            record_swipe(ss, event_id, "liked")
            close_detail(ss)
    else:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✖ Skip", use_container_width=True):
                record_swipe(ss, event_id, "skipped")
                close_detail(ss)
        with c2:
            if st.button("❤ Save", use_container_width=True, type="primary"):
                record_swipe(ss, event_id, "liked")
                close_detail(ss)

    st.caption(
        "Full description above is from the festival's own event card -- "
        "there's no separate ticket/booking link in this dataset.",
    )
