"""Recommendation ranking via semantic search.

Each event in data/vector_database.json carries a precomputed embedding of
its title + full_desc (see embedding_scripts/embedding_openai.py), via
OpenAI's embedding API. Queries are embedded with the same
`OpenAIEmbeddings` model below -- query and document vectors have to come
from the same embedding space for cosine similarity to mean anything, so
if this ever changes, embedding_openai.py needs to change with it (and
vector_database.json needs regenerating).
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
from langchain_openai import OpenAIEmbeddings

from app.models import RecommendationRequest

# NB: app.agent is imported lazily, inside generate_recommendations() below,
# not here at module level. app/agent/__init__.py imports semantic_search
# from this file, so an eager `import app.agent` here creates a circular
# import: whichever of the two modules loads first finds the other only
# half-initialized and fails with "cannot import name ... from partially
# initialized module". Deferring this import to call time (when both
# modules are guaranteed to already be fully loaded) breaks the cycle
# without changing either module's public API.

_VECTOR_DB_PATH = Path(__file__).parent.parent.parent / "data" / "vector_database.json"

model = OpenAIEmbeddings()

def _load_vectors() -> dict[str, np.ndarray]:
    print("Loading vector_database.json...")
    with open(_VECTOR_DB_PATH, encoding="utf-8") as f:
        records = json.load(f)
    return {r["id"]: np.array(r["vector"], dtype=np.float32) for r in records}


_VECTORS_BY_ID: dict[str, np.ndarray] = _load_vectors()

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


def _compute_cos_similarity(document_matrix: np.ndarray, query_vector: np.ndarray) -> np.ndarray:
    norm_matrix = document_matrix / np.linalg.norm(document_matrix, axis=1, keepdims=True)
    norm_query = query_vector / np.linalg.norm(query_vector)
    return np.dot(norm_matrix, norm_query)


def update_query(query_vector: np.ndarray, like_vector: np.ndarray, fac: float = 0.9) -> np.ndarray:
    """Nudge a query vector toward a new signal vector (liked event), weighted by `fac`. Renormalized so repeated calls
    don't drift the vector's magnitude."""
    new_query_vector = fac * query_vector + (1 - fac) * like_vector
    return new_query_vector / np.linalg.norm(new_query_vector)

def _build_query_text(tag_texts: list[str], interests_text: str) -> str:
    """Combine selected categories and the user's free-text description into
    one query string. Both are optional inputs; at least one must be
    non-empty by the time this is called (see the fallback in the caller)."""
    parts = []
    if tag_texts:
        parts.append("Interested in: " + ", ".join(tag_texts) + ".")
    if interests_text.strip():
        parts.append(interests_text.strip())
    return " ".join(parts)

def semantic_search(query_text: str, events: list[dict], top_k: int = 5) -> list[dict]:
    """General-purpose semantic search: the top `top_k` events (full records,
    not just ids) ranked by cosine similarity to `query_text`.

    `generate_recommendations` below ranks the *entire* candidate set for the
    swipe deck; this is the smaller-grained building block for anything that
    just wants "the top few events matching this text" -- e.g. a RAG tool for
    app/agent's LLM agent.
    """
    candidates = [e for e in events if e["id"] in _VECTORS_BY_ID]
    if not candidates:
        return []

    query_vector = np.asarray( model.embed_query(query_text) )
    matrix = np.stack([_VECTORS_BY_ID[c["id"]] for c in candidates])
    similarities = _compute_cos_similarity(matrix, query_vector)

    ranked = sorted(zip(candidates, similarities), key=lambda pair: -pair[1])
    return [e for e, _ in ranked[:top_k]] if top_k else [e for e, _ in ranked]

# How many events the swipe deck actually shows. The catalog has hundreds
# of events; nobody's swiping through all of them, so the RAG step selects
# only its best matches rather than handing back a fully ranked 383-long list.
TOP_K_DISPLAY = 10

def generate_recommendations(
    events: list[dict],
    request: RecommendationRequest,
) -> tuple[list[str], dict[str, int], bool, dict[str, str]]:
    """Returns (ranked_event_ids, match_scores, interests_text_was_valid, match_explanations).

    The third value reflects whether request.interests_text (if any) looked
    like a genuine interests description to the LLM -- see
    app.agent.validate_interests. Invalid text is excluded from the query
    (tags alone are used instead) rather than silently trusted, since it
    otherwise flows straight into an LLM prompt below.

    The fourth is a {event_id: one-sentence "why this matches you"} map for
    the returned events, from app.agent.explain_matches.
    """
    candidates = list(events)
    if request.highlights_only:
        candidates = [e for e in candidates if e.get("highlight") is True]
    candidates = [e for e in candidates if e["id"] in _VECTORS_BY_ID]
    if not candidates:
        return [], {}, True, {}

    from app import agent  # deferred -- see the note near the top of this file

    validation = agent.validate_interests(request.interests_text)
    interests_text = request.interests_text if validation.is_valid else ""

    raw_query = _build_query_text(list(request.tags), interests_text) or "festival event"
    generated_query = agent.ask(f"You are given with the following query: {raw_query}. \
                                You have to generate a query suitable for query-documents matching based on semantic embeddigns. \
                                For better understanding of the events you can also view into some of them by using the tool. \
                                You have to output the answer only with no excess words. The query has to be short.")

    query_vector = np.asarray( model.embed_query(generated_query) )

    matrix = np.stack([_VECTORS_BY_ID[c["id"]] for c in candidates])
    similarities = _compute_cos_similarity(matrix, query_vector)

    # Relevance picks the top-K candidate pool first; "soonest" only
    # reorders *within* that pool -- otherwise it would show the 10
    # chronologically earliest events regardless of whether they have
    # anything to do with what the user asked for.
    scored = sorted(zip(candidates, similarities), key=lambda pair: -pair[1])[:TOP_K_DISPLAY]
    if request.sort_mode == "soonest":
        scored.sort(key=lambda pair: _parse_sort_key(pair[0].get("time")))

    ranked_event_ids = [e["id"] for e, _ in scored]
    # Similarity as a 0-100 "match" score -- still called matched_tag_count
    # on the wire (see RecommendationResponse) to keep the API stable.
    match_scores = {e["id"]: max(0, round(float(sim) * 100)) for e, sim in scored}
    match_explanations = agent.explain_matches(raw_query, [e for e, _ in scored])
    return ranked_event_ids, match_scores, validation.is_valid, match_explanations
