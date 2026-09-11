# Linz Event Recommender -- Frontend

A Streamlit frontend for a Tinder-style event recommender: pick a few
interests, swipe through a ranked deck of Ars Electronica Festival 2026
events, save the ones worth your time. **It's wired to a real backend** --
see `backend/` -- which must be running (`http://localhost:8000` by
default) for this to have data to show.

## Purpose

Built from `event_recommender_frontend_flow (1).svg`, a screen-flow diagram
titled *"Frontend screen flow for the Linz event recommender app"*. The
diagram is a functional spec, not a mockup: five screens, one linear path
and two branches, described in its own `<desc>` as --

> Landing screen leads to interest selection, then the main swipe screen,
> which branches to an event detail screen when a card is tapped and to a
> saved events screen from the tab bar, with two-way navigation back to the
> swipe screen.

## Workflow interpretation

| SVG node | App screen | Notes |
|---|---|---|
| Landing screen | `landing` | Hero + "Get started" |
| Interest selection | `interests` | Tag picker + preferences (see assumptions) |
| *(implied by "ranked")* | `generating` | A processing stage the SVG doesn't draw but its copy ("main **ranked** card stack") implies -- something has to do the ranking. Modeled explicitly so loading/failure/retry states have somewhere to live. |
| Swipe screen | `discover` | The ranked card stack, hub of the two branches below |
| Event detail | `detail` | Opened by tapping a card, two-way nav back to Discover |
| Saved events | `saved` | Reached via a tab bar, two-way nav back to Discover |

The sidebar's **Workflow** stepper mirrors the linear part of this
(Landing -> Interests -> Recommendations -> Discover) with live status
badges (`not started / ready / in progress / completed / failed / requires
attention`). Detail and Saved are drill-downs off Discover, not pipeline
stages, so they're surfaced as a tab bar + a metric in the sidebar instead
of stepper nodes -- that matches how the SVG actually draws them (branches,
not a line).

The original SVG itself is viewable from the sidebar ("Workflow diagram
(reference)") for comparison -- it is not the application.

## Assumptions

The SVG specifies *screens and transitions*, not data or ranking logic, so
the following were product-design calls, made explicit here rather than
left implicit in code:

- **"Pick tags & preferences"** (the Interest selection subtitle) was read
  as two things: a multi-select category picker, *and* a small preferences
  block (Curated highlights only / sort order) applied on top of it. It's
  one toggle, not two, because that's what the real data actually supports
  -- see below.
- **Minimum 3 tags** required before continuing -- arbitrary but standard
  for this kind of onboarding; too few tags makes "ranking" meaningless.
- **Ranking heuristic**: an event scores 1 if its `category` is among the
  selected tags, 0 otherwise (each card has exactly one category, not a
  list, so this isn't an overlap count). If every candidate scores 0, all
  are kept at score 0 rather than showing nothing, so users only see a
  truly empty deck when the "Curated highlights only" filter excludes
  *every* remaining event.
- **The "ranked card stack"** implies a ranking step happens somewhere
  before swiping starts. There's no dedicated SVG node for it, so it's
  modeled as its own pipeline stage (`generating`) with a real, interruptible
  backend call -- this is where loading/failure/retry states live, now
  driven by genuine network failures rather than a simulated toggle.
- **Event data** is `data/prepared_cards.json` at the repo root -- 383 real
  Ars Electronica Festival 2026 event cards, served live by `backend/`.
  Each card has exactly one `category` (used as the "tag"), a `highlight`
  flag, and a `location` with venue/area/coordinates -- no organizer,
  price, or child-friendly data exists in this dataset, so the UI doesn't
  claim to filter on things it can't actually know.
- **Ticket/booking links**: not present in this dataset at all, so the
  detail screen doesn't pretend to offer one.

## Architecture

```
frontend/
  app.py                    entry point: page config, global CSS, routing
  requirements.txt
  .streamlit/config.toml    theme
  assets/workflow.svg       the source SVG (metadata-stripped), reference view only
  src/
    types/models.py         Event, EventLocation, TagInfo, StageInfo, Screen/StageStatus literals
    data/
      loader.py              fetches from backend/, cached (ttl) -> list[Event] / list[TagInfo]
    utils/
      backend_client.py      shared BACKEND_URL / timeout config
      mock_backend.py        POST /recommendations client (name predates the real backend)
      formatting.py          parses prepared_cards.json's German date strings for sorting
      icons.py                category -> emoji, status -> color/icon lookup tables
    hooks/
      state.py                session-state schema, screen transitions, swipe/undo,
                               pipeline status derivation -- the single source of truth
    components/               reusable, presentation-only pieces
      header.py, sidebar.py, hub_tabs.py, event_card.py,
      tag_pill.py, status_badge.py, empty_state.py
    features/                 one folder per screen (the SVG's nodes)
      landing/ interests/ generating/ discover/
      event_detail/ saved_events/ workflow_overview/
      each exposes a single render(ss) -- or render() for the overview
```

`hooks/state.py` is worth reading first: Streamlit reruns the whole script
on every interaction, so it centralizes *where the user is* (`screen`),
*what they've done* (`liked_ids`/`skipped_ids`/`history`), and *how far the
pipeline has gotten* (`gen_status`, `deck`) behind one `AppState` proxy, plus
the stage-status logic the sidebar stepper renders from.

One non-obvious wrinkle documented in that file: Streamlit clears a
widget's session-state value once that widget stops being rendered. Since
the tag/preference pickers only render on the Interests screen, their raw
values would otherwise vanish the moment the user moves on. The "Continue"
button snapshots them into separate `confirmed_*` keys precisely to avoid
that -- everything downstream (ranking, generation) reads the snapshot, not
the live widget keys.

## Running it

Start the backend first (see `backend/README.md`), then:

```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

Override the backend's address with the `BACKEND_URL` env var if it's not
on `http://localhost:8000`.

Tested against `streamlit==1.59.1`. The full workflow (landing -> interests
-> generation success/retry -> swipe/undo/save/skip -> detail -> saved ->
reset) has been verified end-to-end with Streamlit's `AppTest` harness
against a *live* backend instance serving real `prepared_cards.json` data,
plus a manual pass in a real browser.
