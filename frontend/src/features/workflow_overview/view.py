from __future__ import annotations

from pathlib import Path

import streamlit.components.v1 as components
import streamlit as st

_SVG_PATH = Path(__file__).resolve().parents[3] / "assets" / "workflow.svg"

_MAPPING = [
    ("Landing screen", "→", "Landing screen (`landing`)"),
    ("Interest selection", "→", "Interest selection (`interests`)"),
    ("Swipe screen", "→", "Discover (`discover`) -- the ranked card stack"),
    ("Event detail", "↔", "Event detail (`detail`), opened from a card, returns to Discover"),
    ("Saved events", "↔", "Saved events (`saved`), reached from the tab bar"),
]


def render() -> None:
    st.markdown("#### Workflow overview")
    st.caption(
        "This is the original screen-flow diagram this app was built from -- kept here for "
        "reference only. It is not the application itself."
    )

    if _SVG_PATH.exists():
        svg_markup = _SVG_PATH.read_text(encoding="utf-8")
        components.html(
            f'<div style="background:#fff;border:1px solid #E7E5DC;border-radius:12px;padding:12px;">{svg_markup}</div>',
            height=440,
            scrolling=True,
        )
    else:
        st.warning("workflow.svg not found in assets/.")

    st.write("")
    st.markdown("**Node → screen mapping**")
    for node, arrow, screen in _MAPPING:
        st.markdown(f"- `{node}` {arrow} {screen}")

    if st.button("Close overview"):
        # Deferred: the sidebar checkbox owns the "show_overview" key and has
        # already rendered by the time this button is clicked, so writing to
        # it here would raise. Flip it at the top of the *next* run instead,
        # before that checkbox is instantiated (see app.py).
        st.session_state["_close_overview_requested"] = True
        st.rerun()
