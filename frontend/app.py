"""Entry point for the Linz Event Recommender frontend -- swipe-first fork.

This is an experimental variant of ../frontend/, isolated here so the
original stays untouched and this is trivially reversible (just delete this
folder). Two differences from the original:

1. No sidebar -- the pipeline stepper, activity metrics, workflow-diagram
   viewer and dev backend-simulation panel are all gone. A single "Restart"
   button in the header (see components/header.py) replaces the sidebar's
   reset button; nothing else has a UI replacement.
2. The Discover screen's cards are real drag-to-swipe gestures (see
   components/swipe_deck.py), matching the interaction in
   `index (1).html` at the repo root, instead of static cards with
   Skip/Save buttons.

Run with: streamlit run app.py (from this folder).
"""
import streamlit as st

st.set_page_config(
    page_title="Linz Event Recommender",
    page_icon="🎪",
    layout="centered",
    initial_sidebar_state="collapsed",
)

from src.components.header import render_app_header  # noqa: E402
from src.features.discover import view as discover_view  # noqa: E402
from src.features.event_detail import view as event_detail_view  # noqa: E402
from src.features.generating import view as generating_view  # noqa: E402
from src.features.interests import view as interests_view  # noqa: E402
from src.features.landing import view as landing_view  # noqa: E402
from src.features.saved_events import view as saved_events_view  # noqa: E402
from src.hooks.state import apply_pending_reset, init_state  # noqa: E402

_SCREEN_RENDERERS = {
    "landing": landing_view.render,
    "interests": interests_view.render,
    "generating": generating_view.render,
    "discover": discover_view.render,
    "detail": event_detail_view.render,
    "saved": saved_events_view.render,
}


def _inject_global_css() -> None:
    st.markdown(
        """
<style>
  .stApp { background: linear-gradient(180deg, #14121F 0%, #1B1830 100%); }
  .block-container { padding-top: 1.6rem; padding-bottom: 3rem; max-width: 640px; }
  h1, h2, h3, h4, p, span, label, .stMarkdown { color: #F3F1FF; }
  button[kind="primary"] {
    border-radius: 999px; border: none;
    background: linear-gradient(90deg,#EC4899,#8B5CF6) !important;
  }
  button[kind="secondary"] { border-radius: 999px; background: #262433; color: #F3F1FF; border: 1px solid #3A3656; }
  div[data-testid="stButton"] > button { border-radius: 999px; }
  div[data-testid="stTextArea"] textarea, div[data-testid="stTextInput"] input {
    background: #1E1B31; color: #F3F1FF; border-radius: 14px; border: 1px solid #3A3656;
  }
  [data-testid="stMetricValue"] { font-size: 1.3rem; }
  div[data-baseweb="tab-list"] { gap: 4px; }
</style>
""",
        unsafe_allow_html=True,
    )


def main() -> None:
    _inject_global_css()
    ss = init_state()

    # Consume any deferred reset request before any widget bound to a
    # _DEFAULTS key is instantiated this run (see reset_workflow()'s
    # docstring in hooks/state.py for why this can't just happen inline).
    apply_pending_reset()

    render_app_header(ss.screen)
    _SCREEN_RENDERERS[ss.screen](ss)


if __name__ == "__main__":
    main()
