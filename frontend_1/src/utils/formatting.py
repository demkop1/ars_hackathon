from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

_MONTHS_DE = {
    "Januar": 1, "Februar": 2, "März": 3, "April": 4, "Mai": 5, "Juni": 6,
    "Juli": 7, "August": 8, "September": 9, "Oktober": 10, "November": 11, "Dezember": 12,
}
_TIME_RE = re.compile(r"(\d+)\.\s+(\w+)\s+(\d{4})\s+(\d{1,2}):(\d{2})")


def parse_event_datetime(time_str: Optional[str]) -> Optional[datetime]:
    """'9. September 2026 15:15 (MESZ) -> 16:15' -> datetime(2026, 9, 9, 15, 15).

    prepared_cards.json's `time` field is already display-ready (used as-is
    in the UI), so this exists only to get a sortable value out of it for
    "Soonest date" sorting -- not for reformatting what's shown to the user.
    """
    if not time_str:
        return None
    match = _TIME_RE.match(time_str)
    if not match:
        return None
    day, month_name, year, hour, minute = match.groups()
    month = _MONTHS_DE.get(month_name)
    if month is None:
        return None
    try:
        return datetime(int(year), month, int(day), int(hour), int(minute))
    except ValueError:
        return None
