"""Entry point for the Linz Event Recommender frontend template.

No backend exists yet -- see src/utils/mock_backend.py and src/data/loader.py
for exactly where a real API would plug in. Run with:

    streamlit run app.py
"""
import streamlit as st

st.set_page_config(
    page_title="Linz Event Recommender",
    page_icon="🎪",
    layout="centered",
    initial_sidebar_state="expanded",
)

from src.components.header import render_app_header  # noqa: E402
from src.components.sidebar import render_sidebar  # noqa: E402
from src.features.discover import view as discover_view  # noqa: E402
from src.features.event_detail import view as event_detail_view  # noqa: E402
from src.features.generating import view as generating_view  # noqa: E402
from src.features.interests import view as interests_view  # noqa: E402
from src.features.landing import view as landing_view  # noqa: E402
from src.features.saved_events import view as saved_events_view  # noqa: E402
from src.features.workflow_overview import view as workflow_overview_view  # noqa: E402
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
  .block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 760px; }
  button[kind="primary"] { border-radius: 10px; }
  button[kind="secondary"] { border-radius: 10px; }
  div[data-testid="stButton"] > button { border-radius: 10px; }
  [data-testid="stSidebar"] { border-right: 1px solid #ECEAE1; }
  [data-testid="stMetricValue"] { font-size: 1.3rem; }
  div[data-baseweb="tab-list"] { gap: 4px; }
</style>
""",
        unsafe_allow_html=True,
    )


def main() -> None:
    _inject_global_css()
    ss = init_state()

    # Consume any deferred state changes *before* the widgets that own those
    # keys are instantiated in render_sidebar() below (see reset_workflow()
    # and workflow_overview's "Close" button for why this is deferred).
    apply_pending_reset()
    if st.session_state.pop("_close_overview_requested", False):
        st.session_state["show_overview"] = False

    render_sidebar(ss)

    if ss.show_overview:
        workflow_overview_view.render()
        return

    render_app_header(ss.screen)
    _SCREEN_RENDERERS[ss.screen](ss)


if __name__ == "__main__":
    main()
