from __future__ import annotations

from typing import Optional

import streamlit as st


def render_empty_state(
    *,
    icon: str,
    title: str,
    message: str,
    action_label: Optional[str] = None,
    key: Optional[str] = None,
) -> bool:
    """Renders a centered empty/completion/error panel. Returns True if the
    optional action button was clicked this run."""
    st.markdown(
        f"""
<div style="text-align:center;padding:48px 24px;background:#FAF9F5;border:1px dashed #DEDCD3;
     border-radius:16px;">
  <div style="font-size:40px;">{icon}</div>
  <div style="font-size:17px;font-weight:700;color:#1F1E1A;margin-top:10px;">{title}</div>
  <div style="font-size:14px;color:#7A7871;margin-top:6px;max-width:440px;margin-left:auto;margin-right:auto;">{message}</div>
</div>
""",
        unsafe_allow_html=True,
    )
    if action_label:
        _, mid, _ = st.columns([1, 1, 1])
        with mid:
            return st.button(action_label, use_container_width=True, key=key)
    return False
