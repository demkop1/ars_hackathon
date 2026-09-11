from __future__ import annotations

import streamlit as st

from src.utils.icons import tag_icon


def tag_pills_html(tags: list[str], *, muted: bool = False) -> str:
    bg, fg, border = ("#F1F1EF", "#5B5952", "#E4E2D9") if muted else ("#EEEDFE", "#534AB7", "#D9D6F7")
    spans = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:4px;background:{bg};color:{fg};'
        f'border:1px solid {border};border-radius:999px;padding:3px 10px;font-size:12px;'
        f'font-weight:500;margin:0 6px 6px 0;white-space:nowrap;">{tag_icon(t)} {t}</span>'
        for t in tags
    )
    return f'<div style="display:flex;flex-wrap:wrap;">{spans}</div>'


def render_tag_pills(tags: list[str], *, muted: bool = False) -> None:
    st.markdown(tag_pills_html(tags, muted=muted), unsafe_allow_html=True)
