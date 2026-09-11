from __future__ import annotations

import streamlit as st

from src.data.loader import load_tags
from src.hooks.state import MIN_TAGS_REQUIRED, AppState, go_to
from src.utils.icons import tag_icon


def render(ss: AppState) -> None:
    tags = load_tags()
    tag_names = [t.name for t in tags]

    st.markdown("#### What are you into?")
    st.caption(
        f"Pick at least {MIN_TAGS_REQUIRED} tags so we can rank your swipe deck. "
        "You can always come back and change this later."
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
    if n_selected < MIN_TAGS_REQUIRED:
        st.warning(
            f"Select at least {MIN_TAGS_REQUIRED} tags to continue "
            f"({n_selected}/{MIN_TAGS_REQUIRED} selected).",
            icon="⚠️",
        )
    else:
        st.success(f"{n_selected} interests selected -- you're ready to continue.", icon="✅")

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
            disabled=n_selected < MIN_TAGS_REQUIRED,
        ):
            # Snapshot into stable keys -- see the comment on confirmed_* in
            # hooks/state.py for why this can't just be read back later.
            ss.confirmed_tags = list(selected or [])
            ss.confirmed_highlights_only = ss.pref_highlights_only
            ss.confirmed_sort_mode = ss.pref_sort_mode
            go_to("generating")
