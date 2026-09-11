from __future__ import annotations

import streamlit as st

from src.components.empty_state import render_empty_state
from src.components.event_card import render_event_card
from src.components.hub_tabs import render_hub_tabs
from src.data.loader import events_by_id
from src.hooks.state import AppState, go_to, open_detail, remove_saved


def render(ss: AppState) -> None:
    render_hub_tabs(ss)
    st.write("")

    if not ss.liked_ids:
        clicked = render_empty_state(
            icon="🤍",
            title="No saved events yet",
            message="Swipe right (❤ Save) on something you like in Discover and it'll show up here.",
            action_label="Go to Discover",
            key="empty_saved_go",
        )
        if clicked:
            go_to("discover")
        return

    events = events_by_id()
    sort_mode = st.selectbox(
        "Sort by",
        options=["Recently saved", "Soonest date"],
        label_visibility="collapsed",
    )
    ids = list(ss.liked_ids)
    if sort_mode == "Soonest date":
        ids.sort(key=lambda i: events[i].next_date or "9999")

    st.caption(f"{len(ids)} saved event{'s' if len(ids) != 1 else ''}")

    for event_id in ids:
        if event_id not in events:
            continue
        event = events[event_id]
        with st.container(border=False):
            render_event_card(event, variant="compact")
            b1, b2, _ = st.columns([1, 1, 2])
            with b1:
                if st.button("View details", key=f"view_{event_id}", use_container_width=True):
                    open_detail(ss, event_id, "saved")
            with b2:
                if st.button("Remove", key=f"remove_{event_id}", use_container_width=True):
                    remove_saved(ss, event_id)
                    st.rerun()
        st.write("")
