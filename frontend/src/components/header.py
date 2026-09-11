from __future__ import annotations

import streamlit as st

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
    st.markdown(
        f"""
<div style="display:flex;align-items:center;justify-content:space-between;
     padding-bottom:14px;margin-bottom:18px;border-bottom:1px solid #ECEAE1;">
  <div style="display:flex;align-items:center;gap:12px;">
    <div style="font-size:26px;">🎪</div>
    <div>
      <div style="font-size:13px;font-weight:700;color:#534AB7;letter-spacing:.03em;text-transform:uppercase;">
        Linz Event Recommender
      </div>
      <div style="font-size:20px;font-weight:700;color:#1F1E1A;line-height:1.2;">{title}</div>
    </div>
  </div>
  <div style="font-size:13px;color:#9A978C;max-width:280px;text-align:right;display:none;">{subtitle}</div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.caption(subtitle)
