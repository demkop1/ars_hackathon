from __future__ import annotations

import streamlit as st

from src.hooks.state import AppState, go_to


def render_hub_tabs(ss: AppState) -> None:
    """Tab bar switching between Discover and Saved events -- the two screens
    the SVG shows branching off the swipe screen, two-way navigable."""
    c1, c2 = st.columns(2)
    with c1:
        if st.button(
            "🔥 Discover",
            key="hub_tab_discover_btn",
            use_container_width=True,
            type="primary" if ss.screen == "discover" else "secondary",
        ):
            if ss.screen != "discover":
                go_to("discover")
    with c2:
        if st.button(
            f"❤️ Saved ({len(ss.liked_ids)})",
            key="hub_tab_saved_btn",
            use_container_width=True,
            type="primary" if ss.screen == "saved" else "secondary",
        ):
            if ss.screen != "saved":
                go_to("saved")
