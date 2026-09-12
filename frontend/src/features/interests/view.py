from __future__ import annotations

import streamlit as st

from src.data.loader import load_tags
from src.hooks.state import AppState, go_to
from src.utils.icons import tag_icon


def render(ss: AppState) -> None:
    tags = load_tags()
    tag_names = [t.name for t in tags]

    st.markdown("#### What are you into?")
    st.caption(
        "Optional -- pick a few categories to steer your swipe deck, or skip "
        "straight to describing your interests below. You can always come "
        "back and change this later."
    )

    selected = st.pills(
        "Interest tags",
        options=tag_names,
        selection_mode="multi",
        key="selected_tags",
        format_func=lambda name: f"{tag_icon(name)} {name}",
        label_visibility="collapsed",
    )

    n_selected = len(selected or [])
    if n_selected:
        st.caption(f"{n_selected} tag{'s' if n_selected != 1 else ''} selected.")

    st.write("")
    st.markdown("#### Anything more specific?")
    st.caption(
        "Optional -- describe what you're in the mood for in your own words. "
        "This is matched semantically alongside your selected tags."
    )
    st.text_area(
        "Describe your interests",
        key="interests_text",
        placeholder="e.g. something hands-on and playful for the evening, or a deep dive into AI ethics",
        label_visibility="collapsed",
        height=80,
    )

    st.write("")
    st.markdown("#### Preferences")
    st.caption("Optional filters applied on top of your interests.")
    st.toggle("Curated highlights only", key="pref_highlights_only")

    st.radio(
        "Sort deck by",
        options=["best_match", "soonest"],
        format_func=lambda v: "Best match first" if v == "best_match" else "Soonest date first",
        key="pref_sort_mode",
        horizontal=True,
    )

    st.write("")
    back_col, spacer, next_col = st.columns([1, 2, 1])
    with back_col:
        if st.button("← Back", use_container_width=True):
            go_to("landing")
    with next_col:
        if st.button(
            "Continue →",
            type="primary",
            use_container_width=True,
        ):
            # Snapshot into stable keys -- see the comment on confirmed_* in
            # hooks/state.py for why this can't just be read back later.
            ss.confirmed_tags = list(selected or [])
            ss.confirmed_interests_text = ss.interests_text
            ss.confirmed_highlights_only = ss.pref_highlights_only
            ss.confirmed_sort_mode = ss.pref_sort_mode
            go_to("generating")
