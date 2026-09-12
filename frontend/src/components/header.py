from __future__ import annotations

import streamlit as st

from src.hooks.state import reset_workflow
from src.types.models import Screen

_SCREEN_TITLES: dict[Screen, tuple[str, str]] = {
    "landing": ("Welcome", "Find events in Linz worth showing up for."),
    "interests": ("Interest selection", "Pick tags & preferences so we can tailor your deck."),
    "generating": ("Curating your deck", "Matching events to what you picked."),
    "discover": ("Discover", "Your ranked stack of Linz events."),
    "detail": ("Event detail", "Full info for this event."),
    "saved": ("Saved events", "Everything you've liked so far."),
}


def render_app_header(screen: Screen) -> None:
    title, subtitle = _SCREEN_TITLES.get(screen, ("", ""))
    left, right = st.columns([5, 1])
    with left:
        st.markdown(
            f"""
<div style="display:flex;align-items:center;gap:12px;padding-bottom:2px;">
  <div style="font-size:26px;">🎪</div>
  <div>
    <div style="font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;
         background:linear-gradient(90deg,#EC4899,#8B5CF6);-webkit-background-clip:text;
         background-clip:text;color:transparent;">
      Discover Ars
    </div>
    <div style="font-size:20px;font-weight:800;color:#F3F1FF;line-height:1.2;">{title}</div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
    with right:
        st.write("")
        if st.button("↺ Restart", use_container_width=True):
            reset_workflow()
    st.markdown(
        f'<div style="font-size:13px;color:#A9A6C2;margin:2px 0 18px 0;'
        f'padding-bottom:14px;border-bottom:1px solid #2E2B45;">{subtitle}</div>',
        unsafe_allow_html=True,
    )
