# Mock Backend

A real, runnable FastAPI service standing in for the eventual recommender
backend. It's a "mock" in that its data is a static, trimmed snapshot and
its ranking logic is the same simple tag-overlap heuristic the frontend
used to simulate locally -- but it's a real HTTP API, not a stub, so the
frontend can be pointed at it with no surprises later.

**The frontend is not wired to call this yet.** It still uses its own
bundled copy of this data and its own local ranking simulation
(`frontend/src/data/loader.py`, `frontend/src/utils/mock_backend.py`). See
"Connecting the frontend" below for that step.

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness check |
| GET | `/events` | All events |
| GET | `/events/{event_id}` | One event, 404 if missing |
| GET | `/tags` | All tags with event counts |
| POST | `/recommendations` | Ranked event ids for a set of tags + preferences |

`POST /recommendations` body:

```json
{
  "tags": ["Museen & Ausstellungen", "Führungen & Touren"],
  "free_only": false,
  "family_only": false,
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

## Structure

```
backend/
  requirements.txt
  app/
    main.py            FastAPI() instance, wires the three routers
    models.py           Pydantic schemas -- field names mirror
                         frontend/src/types/models.py (Event, TagInfo, Preferences)
                         on purpose, so the frontend's existing parsing keeps working
    store.py             in-memory data store, loaded once at startup from app/data/
    ranking.py            the tag-overlap scoring logic, ported 1:1 from
                          frontend/src/utils/mock_backend.py
    data/
      events.json         same trimmed Linz event snapshot the frontend bundles
      tags.json
    routes/
      events.py
      tags.py
      recommendations.py
```

## Connecting the frontend

Only two frontend files need to change, and only their internals -- nothing
that calls them does, since they already only depend on function
signatures:

- `frontend/src/data/loader.py`: replace the local JSON reads in
  `load_events()` / `load_tags()` with `GET /events` / `GET /tags` calls
  (still parsed into the same `Event`/`TagInfo` objects, still wrapped in
  `st.cache_data`, now with a `ttl=` instead of caching forever).
- `frontend/src/utils/mock_backend.py`: replace the sleep+scoring body of
  `generate_recommendations()` with a `POST /recommendations` call,
  catching connection/timeout errors and re-raising as the existing
  `RecommendationError` -- that's what keeps `generating/view.py`'s
  failure/retry UI working unchanged.

No CORS setup is needed on this side: those calls happen from Streamlit's
Python process (server-to-server), not from the browser.

## Growing this into something real

- **Real data**: `store.py`'s `_load()` is the one place that knows the
  data is static JSON -- point it at `data/Linztermine.json` or
  `data/notion_export.json` at the repo root instead (or a DB) and nothing
  else changes.
- **Persistence**: there's currently no way to save a user's liked/skipped
  events server-side -- add that once the frontend needs saves to survive
  a restart or be shared across users. SQLite is enough to start; no need
  to reach further than that for a hackathon.
