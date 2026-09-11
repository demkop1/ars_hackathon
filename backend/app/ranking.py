"""Recommendation ranking.

prepared_cards.json has one `category` per card (not a list of tags) and no
price/child-friendly flags -- only a `highlight` bool -- so scoring is a
simple category-membership check and filtering is a single toggle, not the
overlap-count + two-filter logic an older, differently-shaped dataset used.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from app.models import RecommendationRequest

import json
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")

# embedding = model.encode(example_tags, prompt_name="query").flatten()

# print("Opening Vector_Database.json...")
# with open("Vector database/vector_database.json", "r", encoding="utf-8") as file:
#     event_list = json.load(file)

# matrix_list = []
# for event in event_list:
#     matrix_list.append(event["vector"])

# matrix = np.array(matrix_list)

# cos_sim = compute_cos_similarity(matrix, embedding)
# top_indices = np.argsort(cos_sim)[::-1][:3]

# for idx in top_indices:
#     print(f"Match: {cos_sim[idx]:.4f} | {event_list[idx]['title']}")

_MONTHS_DE = {
    "Januar": 1, "Februar": 2, "März": 3, "April": 4, "Mai": 5, "Juni": 6,
    "Juli": 7, "August": 8, "September": 9, "Oktober": 10, "November": 11, "Dezember": 12,
}
_TIME_RE = re.compile(r"(\d+)\.\s+(\w+)\s+(\d{4})\s+(\d{1,2}):(\d{2})")


def _parse_sort_key(time_str: Optional[str]) -> str:
    """'9. September 2026 15:15 (MESZ) -> 16:15' -> '20260909 1515' (sortable).
    Falls back to a key that sorts last for anything unparseable."""
    if not time_str:
        return "99999999 9999"
    match = _TIME_RE.match(time_str)
    if not match:
        return "99999999 9999"
    day, month_name, year, hour, minute = match.groups()
    month = _MONTHS_DE.get(month_name, 0)
    try:
        datetime(int(year), month, int(day), int(hour), int(minute))
    except ValueError:
        return "99999999 9999"
    return f"{int(year):04d}{month:02d}{int(day):02d} {int(hour):02d}{int(minute):02d}"


def _compute_cos_similarity(document_matrix, query_vector):
    norm_matrix = document_matrix / np.linalg.norm(document_matrix, axis=1, keepdims=True)
    norm_embedding = query_vector/np.linalg.norm(query_vector)

    return np.dot(norm_matrix, norm_embedding)

def update_query(query_vector, like_vector, fac=0.9):
   new_query_vector = fac * query_vector + (1-fac) * like_vector
   return new_query_vector / np.linalg.norm(new_query_vector)

def generate_recommendations(
    events: list[dict],
    request: RecommendationRequest,
) -> tuple[list[str], dict[str, int]]:
    selected_categories = set(request.tags)

    candidates = list(events)
    if request.highlights_only:
        candidates = [e for e in candidates if e.get("highlight") is True]

    scored = [(e, _score(e, selected_categories)) for e in candidates]
    scored = [(e, s) for e, s in scored if s > 0] or [(e, 0) for e in candidates]

    if request.sort_mode == "soonest":
        scored.sort(key=lambda pair: (_parse_sort_key(pair[0].get("time")), -pair[1]))
    else:
        scored.sort(key=lambda pair: (-pair[1], _parse_sort_key(pair[0].get("time"))))

    ranked_event_ids = [e["id"] for e, _ in scored]
    matched_tag_count = {e["id"]: s for e, s in scored}
    return ranked_event_ids, matched_tag_count
