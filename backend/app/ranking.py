"""Recommendation ranking via semantic search.

Each event in data/vector_database.json carries a precomputed embedding of
its `embedding_input` text (see embedding_scripts/embedding_qwen.py). To
rank, we embed the user's selected tags as *query* vectors (Qwen3-Embedding
uses an asymmetric query/document scheme -- documents were embedded plain,
queries need `prompt_name="query"` to get the matching retrieval behavior),
blend them into one combined query vector, and rank candidates by cosine
similarity to it.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from langchain_openai import OpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings

import dotenv
dotenv.load_dotenv()

from app.models import RecommendationRequest

_VECTOR_DB_PATH = Path(__file__).parent.parent.parent / "data" / "vector_database.json"

# print("Loading Qwen3-Embedding-0.6B model...")
# model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")
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


def _combined_query_vector(tag_vectors: np.ndarray) -> np.ndarray:
    """Blend N equally-important tag embeddings into one query vector.

    Applying `update_query` with fac=k/(k+1) at the k-th step is exactly the
    incremental-mean formula, so this ends up as a true running average over
    all N tags -- not just whichever tag happened to be encoded first.
    """
    query_vector = tag_vectors[0]
    for k, vector in enumerate(tag_vectors[1:], start=1):
        query_vector = update_query(query_vector, vector, fac=k / (k + 1))
    return query_vector

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
    app/agent.py's LLM agent.
    """
    candidates = [e for e in events if e["id"] in _VECTORS_BY_ID]
    if not candidates:
        return []

    query_vector = np.asarray( model.embed_query(query_text, prompt_name="query") )
    matrix = np.stack([_VECTORS_BY_ID[c["id"]] for c in candidates])
    similarities = _compute_cos_similarity(matrix, query_vector)

    ranked = sorted(zip(candidates, similarities), key=lambda pair: -pair[1])
    return [e for e, _ in ranked[:top_k]]


def generate_recommendations(
    events: list[dict],
    request: RecommendationRequest,
) -> tuple[list[str], dict[str, int]]:
    candidates = list(events)
    if request.highlights_only:
        candidates = [e for e in candidates if e.get("highlight") is True]
    candidates = [e for e in candidates if e["id"] in _VECTORS_BY_ID]
    if not candidates:
        return [], {}

    query_text = _build_query_text(list(request.tags), request.interests_text) or "festival event"
    query_vector = np.asarray(model.encode(query_text, prompt_name="query"))

    matrix = np.stack([_VECTORS_BY_ID[c["id"]] for c in candidates])
    similarities = _compute_cos_similarity(matrix, query_vector)

    scored = list(zip(candidates, similarities))
    if request.sort_mode == "soonest":
        scored.sort(key=lambda pair: (_parse_sort_key(pair[0].get("time")), -pair[1]))
    else:
        scored.sort(key=lambda pair: -pair[1])

    ranked_event_ids = [e["id"] for e, _ in scored]
    # Similarity as a 0-100 "match" score -- still called matched_tag_count
    # on the wire (see RecommendationResponse) to keep the API stable.
    match_scores = {e["id"]: max(0, round(float(sim) * 100)) for e, sim in scored}
    return ranked_event_ids, match_scores
