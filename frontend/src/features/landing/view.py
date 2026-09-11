from __future__ import annotations

import streamlit as st

from src.data.loader import load_events
from src.hooks.state import AppState, go_to

_HIGHLIGHTS = [
    ("🧭", "Curated from Linz", "Real events pulled from the city's public listings."),
    ("🎯", "Matched to you", "Swipe decks are ranked by the interests you pick."),
    ("❤️", "Nothing gets lost", "Save events as you go and revisit them anytime."),
]


def render(ss: AppState) -> None:
    events = load_events()
    st.markdown(
        f"""
<div style="background:linear-gradient(135deg,#EEEDFE 0%,#E1F5EE 100%);border-radius:20px;
     padding:44px 36px;text-align:center;margin-bottom:28px;">
  <div style="font-size:44px;">🎪</div>
  <div style="font-size:30px;font-weight:800;color:#1F1E1A;margin-top:8px;">Discover Linz, one swipe at a time</div>
  <div style="font-size:15px;color:#5B5952;margin-top:10px;max-width:560px;margin-left:auto;margin-right:auto;">
    Tell us what you're into, then swipe through a ranked stack of {len(events)}+ local events --
    exhibitions, tours, markets, concerts and more -- and save the ones worth your evening.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    cols = st.columns(3)
    for col, (icon, title, desc) in zip(cols, _HIGHLIGHTS):
        with col:
            st.markdown(
                f"""
<div style="background:#FFFFFF;border:1px solid #E7E5DC;border-radius:14px;padding:18px;height:130px;">
  <div style="font-size:22px;">{icon}</div>
  <div style="font-size:14px;font-weight:700;color:#1F1E1A;margin-top:6px;">{title}</div>
  <div style="font-size:12px;color:#7A7871;margin-top:4px;">{desc}</div>
</div>
""",
                unsafe_allow_html=True,
            )

    st.write("")
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        if st.button("Get started →", type="primary", use_container_width=True):
            go_to("interests")
    st.caption(
        "Next: pick a few interests so we can tailor your swipe deck.",
        help="This mirrors the app's screen flow: Landing → Interest selection → Swipe.",
    )
