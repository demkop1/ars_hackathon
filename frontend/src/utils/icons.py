"""Static lookup tables for emoji/icon & color treatment.

Centralized so components never hardcode a status color twice.
"""
from __future__ import annotations

from src.types.models import StageStatus

TAG_ICONS: dict[str, str] = {
    "Museen & Ausstellungen": "🖼️",
    "Führungen & Touren": "🧭",
    "Spiel & Spaß": "🎲",
    "Zum Mitmachen": "🙌",
    "Wissen & Kurse": "📚",
    "Märkte & Messen": "🛍️",
    "Konzerte & Unterhaltung": "🎤",
    "Gesundheit": "🩺",
    "Kinder & Jugend": "🧒",
    "Zum Zuschauen": "👀",
    "Klassische & traditionelle Musik": "🎻",
    "Kulinarik": "🍽️",
    "Theater & Kabarett": "🎭",
    "Zusammenleben": "🤝",
    "Literatur": "📖",
    "Party & Nightlife": "🪩",
    "Filme & Kino": "🎬",
    "Festivals": "🎪",
    "Feste & Bälle": "🎉",
    "Musicals & Shows": "🎶",
    "Freizeit & Unterhaltung": "🎡",
    "Kunst & Kultur": "🎨",
}
DEFAULT_TAG_ICON = "🏷️"


def tag_icon(tag: str) -> str:
    return TAG_ICONS.get(tag, DEFAULT_TAG_ICON)


# status -> (label, background, text color, border, icon)
STATUS_META: dict[StageStatus, dict[str, str]] = {
    "not_started": {
        "label": "Not started",
        "bg": "#F1F1EF",
        "fg": "#7A7871",
        "border": "#DEDCD3",
        "icon": "○",
    },
    "ready": {
        "label": "Ready",
        "bg": "#EEEDFE",
        "fg": "#534AB7",
        "border": "#C9C5F2",
        "icon": "◐",
    },
    "in_progress": {
        "label": "In progress",
        "bg": "#FFF4E0",
        "fg": "#95590A",
        "border": "#F4D9A3",
        "icon": "◒",
    },
    "completed": {
        "label": "Completed",
        "bg": "#E1F5EE",
        "fg": "#0F6E56",
        "border": "#B7E4D4",
        "icon": "✓",
    },
    "failed": {
        "label": "Failed",
        "bg": "#FBEAEA",
        "fg": "#B3261E",
        "border": "#F2C6C4",
        "icon": "✕",
    },
    "requires_attention": {
        "label": "Requires attention",
        "bg": "#FFF0E5",
        "fg": "#B25E09",
        "border": "#F6D2AE",
        "icon": "!",
    },
}
