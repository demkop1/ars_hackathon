from __future__ import annotations

import streamlit as st

from src.data.loader import load_events
from src.hooks.state import AppState, go_to

# icon, word -- no sentences, just quick doodle-sticker labels
_STICKERS = [
    ("🧭", "Curated", -4),
    ("🎯", "Matched", 3),
    ("❤️", "Saved", -2),
]


def render(ss: AppState) -> None:
    events = load_events()

    stickers_html = "".join(
        f"""
<span style="display:inline-flex;align-items:center;gap:6px;background:#FFFFFF;
     border:2px dashed #C9A6D9;border-radius:14px;padding:7px 14px;margin:4px 6px;
     font-size:13px;font-weight:800;color:#4B3B63;transform:rotate({angle}deg);">
  {icon} {word}
</span>"""
        for icon, word, angle in _STICKERS
    )

    st.markdown(
        f"""
<div style="background:linear-gradient(135deg,#F4E9FB 0%,#E4F4EC 100%);border-radius:22px;
     border:2px dashed #D6BEE8;padding:40px 28px 30px;text-align:center;margin-bottom:22px;">
  <div style="font-size:48px;transform:rotate(-6deg);display:inline-block;">🎪</div>
  <div style="font-size:28px;font-weight:900;color:#241F33;margin-top:6px;letter-spacing:-0.01em;">
    Swipe your way through Linz
  </div>
  <svg width="170" height="10" viewBox="0 0 170 10" style="margin:2px auto 10px;display:block;">
    <path d="M3 6 Q 22 1, 42 6 T 82 6 T 122 6 T 162 6" stroke="#EC4899" stroke-width="3"
          fill="none" stroke-linecap="round"/>
  </svg>
  <div style="font-size:14.5px;color:#5B5169;">
    {len(events)}+ events. Swipe right on what's worth your evening.
  </div>
  <div style="margin-top:16px;">{stickers_html}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        if st.button("Let's go →", type="primary", use_container_width=True):
            go_to("interests")
