"""Draggable swipe-card stack, replicating the gesture physics of
`index (1).html` (the vanilla JS/Tailwind mockup at the repo root) inside
Streamlit, via the `st.components.v2` bidirectional component API.

Unlike `st.components.v1.html` (a sandboxed iframe with no way back to
Python), a `components.v2.component` mounts its JS directly into the page
(in a style-isolated shadow root, not an iframe) and can report a value
back to Python via `setTriggerValue`. A committed swipe -- dragging a card
past the threshold, or tapping the on-card ✕/♥ buttons -- calls
`setTriggerValue('swiped', {"direction": ..., "card_id": ...})`; that
value behaves like `st.button()`'s return value (True for exactly one
render, then back to falsy), so the caller just checks it once per run.
"""
from __future__ import annotations

import html as html_lib
from typing import Optional

import streamlit as st

from src.types.models import Event
from src.utils.icons import tag_icon

_CSS = """
:host, .sd-root { all: initial; font-family: -apple-system, "Segoe UI", sans-serif; }
.sd-deck { position: relative; width: 100%; }
.sd-card {
  position: absolute; inset: 0; background: #FFFFFF; border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0,0,0,0.35); padding: 22px; padding-top: 0;
  display: flex; flex-direction: column; overflow: hidden; color: #1F1E1A;
  box-sizing: border-box; transition: transform 0.3s ease-out, opacity 0.3s ease-out;
  user-select: none;
}
.sd-card.sd-top { cursor: grab; }
.sd-card.sd-top:active { cursor: grabbing; }
.sd-card.sd-flying-right { transform: translate(150vw, -10vh) rotate(30deg) !important; transition: transform .45s ease-in; }
.sd-card.sd-flying-left { transform: translate(-150vw, -10vh) rotate(-30deg) !important; transition: transform .45s ease-in; }
.sd-hero {
  height: 34%; margin: 0 -22px 14px -22px; border-radius: 0;
  background: linear-gradient(135deg, #F4C9E0 0%, #C9C2F2 100%);
  display: flex; align-items: center; justify-content: center; font-size: 52px;
  flex-shrink: 0;
}
.sd-badges { margin-bottom: 8px; display: flex; flex-wrap: wrap; gap: 6px; }
.sd-badge {
  display: inline-flex; align-items: center; border-radius: 999px; padding: 3px 10px;
  font-size: 10px; font-weight: 800; letter-spacing: .03em; white-space: nowrap;
}
.sd-badge-highlight { background: #FFF4E0; color: #95590A; }
.sd-badge-match-hi { background: #E1F5EE; color: #0F6E56; }
.sd-badge-match-mid { background: #EEEDFE; color: #534AB7; }
.sd-badge-match-lo { background: #F1F1EF; color: #5B5952; }
.sd-category { font-size: 11px; font-weight: 800; color: #A6379E; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 4px; }
.sd-title { font-size: 21px; font-weight: 900; line-height: 1.25; margin: 0 0 6px 0; }
.sd-meta { font-size: 12px; color: #7A7871; margin-bottom: 10px; }
.sd-desc {
  font-size: 13.5px; color: #4B4940; line-height: 1.5; flex: 1; overflow: hidden;
  display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical;
}
.sd-explain {
  margin-top: 10px; padding: 9px 11px; background: #F3EBFB; border-left: 3px solid #A855F7;
  border-radius: 8px; font-size: 12px; line-height: 1.45; color: #5B21B6; flex-shrink: 0;
}
.sd-buttons { display: flex; justify-content: center; gap: 28px; margin-top: 18px; }
.sd-btn {
  width: 58px; height: 58px; border-radius: 999px; border: none; cursor: pointer;
  display: flex; align-items: center; justify-content: center; font-size: 22px;
  box-shadow: 0 8px 20px rgba(0,0,0,0.3); transition: transform .15s ease;
}
.sd-btn:hover { transform: scale(1.08); }
.sd-btn-skip { background: #262433; color: #F87171; }
.sd-btn-like { background: linear-gradient(135deg, #EC4899, #8B5CF6); color: white; font-size: 26px; }
.sd-empty { text-align: center; color: #9A978C; padding: 60px 20px; }
"""

_JS = r"""
export default function(component) {
    const { data, setTriggerValue, parentElement } = component;
    const cards = data.cards || [];

    const root = document.createElement('div');
    root.className = 'sd-root';
    parentElement.appendChild(root);

    if (cards.length === 0) {
        root.innerHTML = '<div class="sd-empty">No more events to show.</div>';
        return;
    }

    const deck = document.createElement('div');
    deck.className = 'sd-deck';
    deck.style.height = (data.deckHeight || 480) + 'px';
    root.appendChild(deck);

    // Render back-to-front so later siblings (the front card) paint on top.
    const ordered = [...cards].reverse();
    ordered.forEach((card, i) => {
        const depth = cards.length - 1 - i; // 0 = front/top
        const div = document.createElement('div');
        div.className = 'sd-card' + (depth === 0 ? ' sd-top' : '');
        div.dataset.id = card.id;
        div.innerHTML = card.html;
        if (depth > 0) {
            const offset = depth * 10;
            const scale = 1 - depth * 0.045;
            div.style.transform = `translateY(${offset}px) scale(${scale})`;
            div.style.opacity = String(1 - depth * 0.25);
        }
        deck.appendChild(div);
    });

    const buttons = document.createElement('div');
    buttons.className = 'sd-buttons';
    buttons.innerHTML = `
        <button class="sd-btn sd-btn-skip" id="sd-skip">&times;</button>
        <button class="sd-btn sd-btn-like" id="sd-like">&hearts;</button>
    `;
    root.appendChild(buttons);

    const topCard = deck.querySelector('.sd-top');

    function commit(direction) {
        if (!topCard) return;
        topCard.classList.add(direction === 'right' ? 'sd-flying-right' : 'sd-flying-left');
        setTimeout(() => {
            setTriggerValue('swiped', { direction, card_id: topCard.dataset.id });
        }, 200);
    }

    root.querySelector('#sd-skip').onclick = () => commit('left');
    root.querySelector('#sd-like').onclick = () => commit('right');

    if (topCard) {
        let dragging = false, startX = 0, currentX = 0;

        const onMove = (x) => {
            if (!dragging) return;
            currentX = x;
            const dx = currentX - startX;
            topCard.style.transition = 'none';
            topCard.style.transform = `translateX(${dx}px) rotate(${dx * 0.06}deg)`;
        };
        const onEnd = () => {
            if (!dragging) return;
            dragging = false;
            topCard.style.transition = '';
            const dx = currentX - startX;
            const threshold = Math.min(window.innerWidth * 0.22, 140);
            if (dx > threshold) {
                commit('right');
            } else if (dx < -threshold) {
                commit('left');
            } else {
                topCard.style.transform = 'translateX(0px) rotate(0deg)';
            }
        };

        topCard.addEventListener('mousedown', e => { dragging = true; startX = e.clientX; currentX = startX; });
        window.addEventListener('mousemove', e => onMove(e.clientX));
        window.addEventListener('mouseup', onEnd);
        topCard.addEventListener('touchstart', e => { dragging = true; startX = e.touches[0].clientX; currentX = startX; }, { passive: true });
        topCard.addEventListener('touchmove', e => onMove(e.touches[0].clientX), { passive: true });
        topCard.addEventListener('touchend', onEnd);
    }
}
"""

_component = st.components.v2.component("swipe_deck", css=_CSS, js=_JS)


def _match_badge_html(match_count: Optional[int]) -> str:
    if match_count is None:
        return ""
    tier = "hi" if match_count >= 70 else "mid" if match_count >= 40 else "lo"
    return f'<span class="sd-badge sd-badge-match-{tier}">\U0001f3af {match_count}% match</span>'


def _card_inner_html(event: Event, *, match_count: Optional[int], explanation: Optional[str]) -> str:
    icon = tag_icon(event.category)
    title = html_lib.escape(event.title)
    category = html_lib.escape(event.category)
    time_str = html_lib.escape(event.time)
    venue = html_lib.escape(event.location.venue)
    desc = html_lib.escape(event.preview_text)

    highlight_badge = '<span class="sd-badge sd-badge-highlight">★ CURATOR PICK</span>' if event.highlight else ""
    match_badge = _match_badge_html(match_count)
    badges_row = (
        f'<div class="sd-badges">{highlight_badge}{match_badge}</div>' if (highlight_badge or match_badge) else ""
    )
    explanation_html = (
        f'<div class="sd-explain">\U0001f4a1 {html_lib.escape(explanation)}</div>' if explanation else ""
    )

    return f"""
      <div class="sd-hero">{icon}</div>
      {badges_row}
      <div class="sd-category">{category}</div>
      <h2 class="sd-title">{title}</h2>
      <div class="sd-meta">\U0001f4c5 {time_str} &nbsp;&middot;&nbsp; \U0001f4cd {venue}</div>
      <div class="sd-desc">{desc}</div>
      {explanation_html}
    """


def render_swipe_deck(
    cards: list[Event],
    *,
    match_scores: dict[str, int],
    explanations: dict[str, str],
    height: int = 480,
    key: str,
) -> Optional[dict]:
    """Mount the draggable deck for up to the first 3 `cards` (front card on
    top, next two peeking behind as depth cues). Returns
    `{"direction": "left" | "right", "card_id": ...}` on the exact render a
    swipe (drag or button) just committed, else None -- callers should act
    on it immediately, the same way they would an `st.button()` result.
    """
    stack = cards[:3]
    data = {
        "deckHeight": height,
        "cards": [
            {
                "id": event.id,
                "html": _card_inner_html(
                    event,
                    match_count=match_scores.get(event.id),
                    explanation=explanations.get(event.id),
                ),
            }
            for event in stack
        ],
    }
    result = _component(
        data=data,
        on_swiped_change=lambda: None,
        height=height + 100,
        key=key,
    )
    return result.swiped


def render_deck_progress(current_index: int, total: int) -> None:
    """A row of thin segmented bars (one per card, Instagram/Tinder-story
    style) instead of a plain progress bar -- passed cards fill solid, the
    current one glows, the rest stay dim. Reads at a glance without a
    number fighting for space on top of a bar."""
    if total <= 0:
        return
    segments = []
    for i in range(total):
        if i < current_index:
            style = "background:linear-gradient(90deg,#EC4899,#8B5CF6);opacity:0.55;"
        elif i == current_index:
            style = (
                "background:linear-gradient(90deg,#EC4899,#8B5CF6);"
                "box-shadow:0 0 8px rgba(236,72,153,0.7);"
            )
        else:
            style = "background:#332F4D;"
        segments.append(f'<div style="flex:1;height:5px;border-radius:999px;{style}"></div>')

    st.markdown(
        f"""
<div style="display:flex;align-items:center;gap:14px;margin:2px 0 18px 0;">
  <div style="display:flex;gap:5px;flex:1;">{''.join(segments)}</div>
  <div style="font-size:12px;font-weight:800;color:#C9C5F2;white-space:nowrap;
       background:#262433;border-radius:999px;padding:4px 11px;">
    {current_index + 1} / {total}
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
