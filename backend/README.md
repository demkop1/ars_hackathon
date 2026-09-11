# Backend

A real, runnable FastAPI service for the event recommender. **It's now wired
to the frontend** (`frontend/src/data/loader.py` and
`frontend/src/utils/mock_backend.py` call it over HTTP) and serves real data
-- `data/prepared_cards.json` at the repo root, 383 Ars Electronica Festival
2026 event cards. Ranking is a simple category-membership heuristic; swap it
for something smarter without touching the frontend, since it only depends
on `POST /recommendations`'s request/response shape.

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness check |
| GET | `/events` | All events |
| GET | `/events/{event_id}` | One event, 404 if missing |
| GET | `/tags` | Distinct `category` values with counts |
| POST | `/recommendations` | Ranked event ids for a set of categories + preferences |

An event (`GET /events/{id}`) looks like:

```json
{
  "id": "c3738ddb450c83379f3201d3aa0c858f",
  "title": "WE GUIDE YOU: Homo futuris (EN)",
  "category": "Guided Tour",
  "highlight": false,
  "time": "9. September 2026 15:15 (MESZ) → 16:15",
  "location": {
    "venue": "Ars Electronica Center, Level 0, Guided Tours & Workshops Desk",
    "area": "DANUBE TRIANGLE",
    "lat": 48.30962,
    "lng": 14.28445,
    "services": null
  },
  "preview_text": "...",
  "full_desc": "...",
  "embedding_input": "..."
}
```

Note what's *not* here: no organizer, no price, no child-friendly flag, no
recurring-occurrence count -- `prepared_cards.json` doesn't have those, so
neither does this API. `highlight` (curator-picked events) is the one real
boolean filter available.

`POST /recommendations` body:

```json
{
  "tags": ["Guided Tour", "Concert", "Workshop"],
  "highlights_only": false,
  "sort_mode": "best_match"
}
```

Interactive docs (Swagger UI) are auto-generated at `/docs` once running.

## Running it

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The frontend looks for this at `http://localhost:8000` by default
(override with the `BACKEND_URL` env var on the frontend side).

## Structure

```
backend/
  requirements.txt
  app/
    main.py            FastAPI() instance, wires the three routers
    models.py           Pydantic schemas -- field names mirror
                         frontend/src/types/models.py (Event, EventLocation,
                         TagInfo, Preferences) on purpose, so the frontend's
                         Event.from_dict() parsing keeps working unchanged
    store.py             in-memory data store, loaded once at startup from
                         data/prepared_cards.json at the repo root
    ranking.py            category-membership scoring + highlight filter +
                          German-date-string parsing for "soonest" sort
    routes/
      events.py
      tags.py
      recommendations.py
```

## Growing this into something real

- **Real-er data**: `store.py`'s `_load()` is the one place that knows the
  data is static JSON -- point it at `data/notion_export.json` (the fuller,
  un-trimmed source `prepared_cards.json` was derived from) or a DB instead,
  and nothing downstream changes as long as `get_events()`/`get_tags()`
  keep returning the same shape.
- **Persistence**: there's currently no way to save a user's liked/skipped
  events server-side -- add that once the frontend needs saves to survive
  a restart or be shared across users. SQLite is enough to start; no need
  to reach further than that for a hackathon.
