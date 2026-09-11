from __future__ import annotations

import streamlit as st

from src.hooks.state import AppState, compute_stage_statuses, go_to, reset_workflow
from src.types.models import StageInfo
from src.utils.icons import STATUS_META

_JUMPABLE = {
    "landing": "landing",
    "interests": "interests",
    "discover": "discover",
}
_NON_JUMP_STATUSES = {"not_started"}


def _render_stage_row(stage: StageInfo, *, is_current: bool) -> None:
    meta = STATUS_META[stage.status]
    target_screen = _JUMPABLE.get(stage.id)
    can_jump = target_screen is not None and stage.status not in _NON_JUMP_STATUSES and not is_current

    border = "#534AB7" if is_current else "transparent"
    st.markdown(
        f"""
<div style="border-left:3px solid {border};padding:6px 0 6px 10px;margin-bottom:2px;">
  <div style="display:flex;align-items:center;justify-content:space-between;gap:6px;">
    <span style="font-size:13px;font-weight:{'700' if is_current else '600'};color:#1F1E1A;">{stage.label}</span>
    <span style="font-size:14px;color:{meta['fg']};">{meta['icon']}</span>
  </div>
  <div style="font-size:11px;color:#9A978C;margin-top:1px;">{stage.caption}</div>
</div>
""",
        unsafe_allow_html=True,
    )
    if can_jump:
        if st.button("Go →", key=f"jump_{stage.id}", use_container_width=True):
            go_to(target_screen)


def render_sidebar(ss: AppState) -> None:
    with st.sidebar:
        st.markdown(
            '<div style="font-size:20px;font-weight:800;color:#1F1E1A;">🎪 Linz Events</div>'
            '<div style="font-size:12px;color:#9A978C;margin-bottom:14px;">Swipe-to-discover recommender</div>',
            unsafe_allow_html=True,
        )

        st.markdown("**Workflow**")
        stages = compute_stage_statuses(ss)
        for stage in stages:
            _render_stage_row(stage, is_current=_is_current(stage.id, ss.screen))
        st.divider()

        st.markdown("**Your activity**")
        c1, c2 = st.columns(2)
        c1.metric("Saved", len(ss.liked_ids))
        c2.metric("Skipped", len(ss.skipped_ids))
        if ss.deck:
            st.progress(
                min(ss.deck_index / len(ss.deck), 1.0),
                text=f"Reviewed {min(ss.deck_index, len(ss.deck))}/{len(ss.deck)} events",
            )
        st.divider()

        st.checkbox("📄 Workflow diagram (reference)", key="show_overview")

        with st.expander("⚙️ Backend simulation (dev)"):
            st.caption(
                "There's no real backend yet -- these controls only affect the "
                "mocked 'Curating your deck' step, so you can see loading, "
                "failure and retry states without wiring up an API."
            )
            st.radio(
                "Simulated response",
                options=["off", "always_fail", "random"],
                format_func=lambda v: {
                    "off": "Always succeed",
                    "always_fail": "Always fail",
                    "random": "Randomly fail (~50%)",
                }[v],
                key="sim_fail_mode",
            )
            st.slider("Simulated latency (s)", 0.0, 3.0, key="sim_delay", step=0.1)

        if st.button("↺ Reset workflow", use_container_width=True):
            reset_workflow()


def _is_current(stage_id: str, screen: str) -> bool:
    if stage_id == "recommendations":
        return screen == "generating"
    if stage_id == "discover":
        return screen in ("discover", "detail", "saved")
    return stage_id == screen
