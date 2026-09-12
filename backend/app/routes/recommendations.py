from __future__ import annotations

from fastapi import APIRouter

from app import store
from app.models import RecommendationRequest, RecommendationResponse
from app.ranking import generate_recommendations

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("", response_model=RecommendationResponse)
def create_recommendations(request: RecommendationRequest) -> RecommendationResponse:
    ranked_event_ids, matched_tag_count, interests_valid, match_explanations = generate_recommendations(
        store.get_events(), request
    )
    return RecommendationResponse(
        ranked_event_ids=ranked_event_ids,
        matched_tag_count=matched_tag_count,
        interests_valid=interests_valid,
        match_explanations=match_explanations,
    )
