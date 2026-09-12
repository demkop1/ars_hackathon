from __future__ import annotations

import streamlit as st

from src.components.empty_state import render_empty_state
from src.components.hub_tabs import render_hub_tabs
from src.components.swipe_deck import render_deck_progress, render_swipe_deck
from src.data.loader import events_by_id
from src.hooks.state import (
    AppState,
    go_to,
    record_swipe,
    undo_last_swipe,
)


def render(ss: AppState) -> None:
    render_hub_tabs(ss)

    if not ss.interests_text_valid:
        st.info(
            "The description you typed didn't look like genuine interests, so we based "
            "this deck on your selected tags instead.",
            icon="🤔",
        )

    st.write("")

    if not ss.deck:
        clicked = render_empty_state(
            icon="🔍",
            title="No events match your filters",
            message="Try widening your interests, or turn off 'Curated highlights only' in preferences.",
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

    events = events_by_id()
    remaining_ids = ss.deck[ss.deck_index :]
    remaining_events = [events[eid] for eid in remaining_ids if eid in events]

    render_deck_progress(ss.deck_index, total)

    swipe_result = render_swipe_deck(
        remaining_events,
        match_scores=ss.match_counts,
        explanations=ss.match_explanations,
        key=f"swipe_deck_{ss.deck_index}",
    )
    if swipe_result:
        direction = swipe_result.get("direction")
        card_id = swipe_result.get("card_id")
        current_id = remaining_events[0].id if remaining_events else None
        if card_id == current_id:  # guard against a stale/duplicate replay
            record_swipe(ss, card_id, "liked" if direction == "right" else "skipped")
            st.rerun()

    if st.button("↩ Undo last swipe", disabled=not ss.history):
        undo_last_swipe(ss)
        st.rerun()
