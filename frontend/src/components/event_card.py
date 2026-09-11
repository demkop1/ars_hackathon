from __future__ import annotations

from typing import Literal, Optional

import streamlit as st

from src.types.models import Event
from src.utils.formatting import format_event_date, format_relative_hint
from src.utils.icons import tag_icon
from src.components.tag_pill import tag_pills_html

CardVariant = Literal["swipe", "detail", "compact"]


def _badge(label: str, bg: str, fg: str) -> str:
    return (
        f'<span style="background:{bg};color:{fg};border-radius:999px;padding:3px 10px;'
        f'font-size:11px;font-weight:700;letter-spacing:.02em;white-space:nowrap;">{label}</span>'
    )


def _price_family_badges(event: Event) -> str:
    parts = []
    if event.free_of_charge is True:
        parts.append(_badge("FREE", "#E1F5EE", "#0F6E56"))
    elif event.free_of_charge is False:
        parts.append(_badge("PAID", "#F1F1EF", "#5B5952"))
    if event.suitable_for_children is True:
        parts.append(_badge("FAMILY-FRIENDLY", "#EEEDFE", "#534AB7"))
    return "".join(f'<span style="margin-right:6px;">{p}</span>' for p in parts)


def render_event_card(
    event: Event,
    *,
    variant: CardVariant = "swipe",
    match_count: Optional[int] = None,
) -> None:
    icon = tag_icon(event.tags[0]) if event.tags else "🎫"
    date_str = format_event_date(event.next_date)
    occurrence_hint = format_relative_hint(event.occurrence_count)

    if variant == "compact":
        desc = ""
        max_tags = 3
    elif variant == "detail":
        desc = event.description
        max_tags = len(event.tags)
    else:  # swipe
        desc = event.description[:220] + ("…" if len(event.description) > 220 else "")
        max_tags = 6

    match_html = ""
    if match_count is not None and match_count > 0:
        match_html = (
            f'<div style="margin-top:8px;font-size:12px;color:#0F6E56;font-weight:600;">'
            f"🎯 Matches {match_count} of your interests</div>"
        )

    pad = "14px 16px" if variant == "compact" else "22px 24px"
    title_size = "16px" if variant == "compact" else "22px"

    html = f"""
<div style="background:#FFFFFF;border:1px solid #E7E5DC;border-radius:16px;padding:{pad};
     box-shadow:0 1px 2px rgba(20,18,10,0.04);">
  <div style="display:flex;align-items:flex-start;gap:14px;">
    <div style="flex-shrink:0;width:44px;height:44px;border-radius:12px;background:#F6F5F0;
         display:flex;align-items:center;justify-content:center;font-size:22px;">{icon}</div>
    <div style="flex:1;min-width:0;">
      <div style="font-size:{title_size};font-weight:700;color:#1F1E1A;line-height:1.3;">{event.title}</div>
      <div style="font-size:13px;color:#7A7871;margin-top:2px;">📅 {date_str} &nbsp;·&nbsp; 📍 {event.location_name}</div>
    </div>
  </div>
  <div style="margin-top:12px;">{_price_family_badges(event)}</div>
  {f'<div style="margin-top:12px;font-size:14px;line-height:1.55;color:#3A3833;">{desc}</div>' if desc else ""}
  {f'<div style="margin-top:12px;">{tag_pills_html(list(event.tags[:max_tags]))}</div>' if event.tags else ""}
  {match_html}
  {f'<div style="margin-top:10px;font-size:12px;color:#9A978C;">🗓️ {occurrence_hint} &nbsp;·&nbsp; Hosted by {event.organizer_name}</div>' if variant != "compact" else ""}
</div>
"""
    st.markdown(html, unsafe_allow_html=True)
