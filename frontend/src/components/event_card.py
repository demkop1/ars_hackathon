from __future__ import annotations

from typing import Literal, Optional

import streamlit as st

from src.types.models import Event
from src.utils.icons import tag_icon
from src.components.tag_pill import tag_pills_html

CardVariant = Literal["swipe", "detail", "compact"]


def _badge(label: str, bg: str, fg: str) -> str:
    return (
        f'<span style="background:{bg};color:{fg};border-radius:999px;padding:3px 10px;'
        f'font-size:11px;font-weight:700;letter-spacing:.02em;white-space:nowrap;">{label}</span>'
    )


def _highlight_badge(event: Event) -> str:
    if not event.highlight:
        return ""
    return f'<span style="margin-right:6px;">{_badge("★ CURATOR PICK", "#FFF4E0", "#95590A")}</span>'


def _match_badge(match_count: Optional[int]) -> str:
    """Match strength as a 0-100 semantic-similarity score against the
    user's selected tags + free-text interests (see backend/app/ranking.py)."""
    if match_count is None:
        return ""
    if match_count >= 70:
        bg, fg = "#E1F5EE", "#0F6E56"
    elif match_count >= 40:
        bg, fg = "#EEEDFE", "#534AB7"
    else:
        bg, fg = "#F1F1EF", "#5B5952"
    return f'<span style="margin-right:6px;">{_badge(f"🎯 {match_count}% match", bg, fg)}</span>'


def render_event_card(
    event: Event,
    *,
    variant: CardVariant = "swipe",
    match_count: Optional[int] = None,
) -> None:
    icon = tag_icon(event.category)

    if variant == "compact":
        desc = ""
    elif variant == "detail":
        desc = event.full_desc
    else:  # swipe
        desc = event.preview_text

    pad = "14px 16px" if variant == "compact" else "22px 24px"
    title_size = "16px" if variant == "compact" else "22px"
    location_line = event.location.venue
    if event.location.area:
        location_line += f" ({event.location.area})"

    html = f"""
<div style="background:#FFFFFF;border:1px solid #E7E5DC;border-radius:16px;padding:{pad};
     box-shadow:0 1px 2px rgba(20,18,10,0.04);">
  <div style="display:flex;align-items:flex-start;gap:14px;">
    <div style="flex-shrink:0;width:44px;height:44px;border-radius:12px;background:#F6F5F0;
         display:flex;align-items:center;justify-content:center;font-size:22px;">{icon}</div>
    <div style="flex:1;min-width:0;">
      <div style="font-size:{title_size};font-weight:700;color:#1F1E1A;line-height:1.3;">{event.title}</div>
      <div style="font-size:13px;color:#7A7871;margin-top:2px;">📅 {event.time} &nbsp;·&nbsp; 📍 {location_line}</div>
    </div>
  </div>
  <div style="margin-top:12px;">{_highlight_badge(event)}{_match_badge(match_count)}</div>
  {f'<div style="margin-top:12px;font-size:14px;line-height:1.55;color:#3A3833;">{desc}</div>' if desc else ""}
  <div style="margin-top:12px;">{tag_pills_html([event.category])}</div>
  {f'<div style="margin-top:10px;font-size:12px;color:#9A978C;">🛎️ {event.location.services}</div>' if variant != "compact" and event.location.services else ""}
</div>
"""
    st.markdown(html, unsafe_allow_html=True)
