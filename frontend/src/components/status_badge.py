from __future__ import annotations

import streamlit as st

from src.types.models import StageStatus
from src.utils.icons import STATUS_META


def status_badge_html(status: StageStatus, *, compact: bool = False) -> str:
    meta = STATUS_META[status]
    pad = "1px 8px" if compact else "3px 10px"
    font = "11px" if compact else "12px"
    return (
        f'<span style="display:inline-flex;align-items:center;gap:5px;'
        f'background:{meta["bg"]};color:{meta["fg"]};border:1px solid {meta["border"]};'
        f'border-radius:999px;padding:{pad};font-size:{font};font-weight:600;'
        f'white-space:nowrap;line-height:1.4;">'
        f'<span>{meta["icon"]}</span>{meta["label"]}</span>'
    )


def render_status_badge(status: StageStatus, *, compact: bool = False) -> None:
    st.markdown(status_badge_html(status, compact=compact), unsafe_allow_html=True)
