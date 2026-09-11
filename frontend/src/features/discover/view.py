from __future__ import annotations

import streamlit as st

from src.components.empty_state import render_empty_state
from src.components.event_card import render_event_card
from src.components.hub_tabs import render_hub_tabs
from src.data.loader import events_by_id
from src.hooks.state import (
    AppState,
    current_event_id,
    go_to,
    open_detail,
    record_swipe,
    undo_last_swipe,
)


def render(ss: AppState) -> None:
    render_hub_tabs(ss)
    st.write("")

    if not ss.deck:
        clicked = render_empty_state(
            icon="🔍",
            title="No events match your filters",
            message="Try widening your interests, or turn off 'Free only' / 'Family-friendly only' in preferences.",
            action_label="Adjust interests",
            key="empty_deck_adjust",
        )
        if clicked:
            go_to("interests")
        return

    total = len(ss.deck)
    if ss.deck_index >= total:
        st.markdown(
            f"""
<div style="text-align:center;padding:40px 24px;background:#E1F5EE;border-radius:16px;">
  <div style="font-size:40px;">🎉</div>
  <div style="font-size:18px;font-weight:700;color:#0F6E56;margin-top:8px;">You've reviewed all {total} events!</div>
  <div style="font-size:14px;color:#3A3833;margin-top:6px;">
    Saved {len(ss.liked_ids)} &nbsp;·&nbsp; Skipped {len(ss.skipped_ids)}
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.write("")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("❤️ View saved events", use_container_width=True):
                go_to("saved")
        with c2:
            if st.button("🔁 Review deck again", use_container_width=True):
                ss.deck_index = 0
                st.rerun()
        with c3:
            if st.button("🎯 Refine interests", use_container_width=True):
                go_to("interests")
        return

    st.progress(ss.deck_index / total, text=f"Card {ss.deck_index + 1} of {total}")

    event_id = current_event_id(ss)
    event = events_by_id()[event_id]
    render_event_card(event, variant="swipe", match_count=ss.match_counts.get(event_id))

    st.write("")
    c_skip, c_undo, c_details, c_like = st.columns([1, 0.7, 1, 1])
    with c_skip:
        if st.button("✖ Skip", use_container_width=True):
            record_swipe(ss, event_id, "skipped")
            st.rerun()
    with c_undo:
        if st.button("↩ Undo", use_container_width=True, disabled=not ss.history):
            undo_last_swipe(ss)
            st.rerun()
    with c_details:
        if st.button("ℹ️ Details", use_container_width=True):
            open_detail(ss, event_id, "discover")
    with c_like:
        if st.button("❤ Save", use_container_width=True, type="primary"):
            record_swipe(ss, event_id, "liked")
            st.rerun()
