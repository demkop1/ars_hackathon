# Linz Event Recommender -- Frontend Template

A Streamlit frontend for a Tinder-style event recommender: pick a few
interests, swipe through a ranked deck of Linz events, save the ones worth
your evening. **There is no backend yet** -- this is a fully working,
click-through template with realistic mocked data and a simulated backend
call, built so a real API can be dropped in later without touching the UI.

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
  as two things: a multi-select tag picker, *and* a small preferences
  block (Free events only / Family-friendly only / sort order) applied on
  top of it.
- **Minimum 3 tags** required before continuing -- arbitrary but standard
  for this kind of onboarding; too few tags makes "ranking" meaningless.
- **Ranking heuristic**: score = number of selected tags an event shares,
  tie-broken by date (or sorted purely by date if "Soonest first" is
  chosen). If preference filters (free/family) eliminate every match, all
  remaining candidates are kept at score 0 rather than showing nothing, so
  users only see a truly empty deck when their filters exclude *every*
  event outright.
- **The "ranked card stack"** implies a ranking step happens somewhere
  before swiping starts. There's no dedicated SVG node for it, so it's
  modeled as its own pipeline stage (`generating`) with a simulated,
  interruptible backend call -- this is where loading/failure/retry states
  live (see "Backend simulation" below).
- **Event data** is a real, trimmed static snapshot of the City of Linz's
  public events feed (`Linztermine.json`, see `../data` at the repo root),
  frozen into `src/data/events.json` / `tags.json` so the frontend has no
  live dependency. 70 events, 15 tag categories, all sourced from actual
  listings (titles, descriptions, locations, organizers, dates).
- **Ticket/booking links**: the source data has organizer links, but
  there's no backend to resolve or proxy them yet, so the detail screen
  says so explicitly rather than linking to a dead end.

## Backend simulation

`src/utils/mock_backend.py` is the one function standing in for a real API
(`generate_recommendations`). It's synchronous, takes a configurable delay,
and can be told to fail (always, or ~50% randomly) via a **Backend
simulation (dev)** panel in the sidebar -- this is how the app demonstrates
loading, failure and retry states honestly, without a real backend to
misbehave on cue. Swap its body for an HTTP call when one exists; nothing
else needs to change, since every caller only depends on its signature.

## Architecture

```
frontend/
  app.py                    entry point: page config, global CSS, routing
  requirements.txt
  .streamlit/config.toml    theme
  assets/workflow.svg       the source SVG (metadata-stripped), reference view only
  src/
    types/models.py         Event, TagInfo, StageInfo, Screen/StageStatus literals
    data/
      events.json, tags.json   static mock dataset (real Linz events)
      loader.py              cached loaders -> list[Event] / list[TagInfo]
    utils/
      mock_backend.py        simulated backend call (ranking + fail/delay controls)
      formatting.py          date/occurrence formatting
      icons.py                tag -> emoji, status -> color/icon lookup tables
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

```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

Tested against `streamlit==1.59.1`. The app was built and verified end-to-end
with Streamlit's `AppTest` harness (landing -> interests -> generation
success/failure/retry -> swipe/undo/save/skip -> detail -> saved -> reset,
all exercised programmatically) plus a manual pass in a real browser, so the
full workflow is confirmed completable through the UI, including its edge
states (empty deck, deck exhausted, generation failure).
