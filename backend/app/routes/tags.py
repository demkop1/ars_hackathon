from __future__ import annotations

from fastapi import APIRouter

from app import store
from app.models import TagOut

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[TagOut])
def list_tags() -> list[dict]:
    return store.get_tags()
