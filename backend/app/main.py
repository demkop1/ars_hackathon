"""Mock backend entry point.

Serves the same static, trimmed Linz event snapshot the frontend used to
bundle itself, behind a real HTTP API with the exact ranking behavior of
`frontend/src/utils/mock_backend.py`. The frontend is not wired to call
this yet -- see ../README.md for how to connect it.

Run with: uvicorn app.main:app --reload --port 8000
"""
from __future__ import annotations

from fastapi import FastAPI

from app.routes import events, recommendations, tags

app = FastAPI(
    title="Linz Event Recommender -- Mock Backend",
    description="In-memory mock API standing in for a real recommendation service.",
    version="0.1.0",
)

app.include_router(events.router)
app.include_router(tags.router)
app.include_router(recommendations.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
