# Live Draft Room Page Handoff - 2026-06-09

## What Changed

A separate `Live Draft Room` page was added for mock/live draft tracking.

- Page file: `app/pages/07_live_draft_room.py`
- Route: `/live-draft-room`
- Navigation label: `Live Draft Room`

The existing `/draft-room` route remains `Draft Prep`.

## What Moved

The mock/live draft workflow now belongs on `Live Draft Room`:

- 50-pick draft grid.
- Current pick / current owner / my-turn status.
- Selected pick correction workflow.
- Player search.
- `Mark Drafted`.
- `Replace Pick`.
- `Undo Last`.
- `Reset Mock`.
- Best remaining / scouting pool.
- Hide drafted toggle.
- Position and source-type filters.
- My upcoming picks.
- Recent picks.
- Save / load / duplicate / clear mock tools.
- Draft state and remaining pool CSV exports.
- Advanced session/source details.

## What Stayed In Draft Prep

Draft Prep remains planning-only:

- Pick cards for `1.03`, `1.04`, `2.04`, `2.08`, and `5.04`.
- Scouting prep source cards.
- Candidate windows.
- Main scouting prep table.
- League history context.
- Advanced audit receipts.
- A collapsed pointer to the separate Live Draft Room page.

Draft Prep does not render the full mock/live workflow by default and does not mutate draft state.

## Draft State Storage Behavior

Live Draft Room uses existing session/local mock storage services:

- `app/components/draft_session.py`
- `src/services/draft_state_service.py`
- `src/services/mock_draft_storage_service.py`
- `src/services/draft_ux_service.py`

State rules:

- In-browser draft state lives in Streamlit session state.
- Live Draft Room uses a separate `live-draft-room::...` session-key namespace.
- Saved mocks are local JSON files under mock draft storage.
- CSV downloads are exports only.
- Active data packs are not mutated.
- Scouting prep rows are read-only inputs to session state.

## Source Readiness State

Live Draft Room shows:

- Draft shape: `5 rounds x 10 teams`.
- Total picks: `50`.
- My picks: `1.03`, `1.04`, `2.04`, `2.08`, `5.04`.
- Scouting pool: loaded from `local_exports/model_v4/draft_prep/latest/scouting_prep_pool_review_rows.csv`.
- Legal pool: pending.
- Dropped veterans: missing.
- Draft state: session/local mock state only.

## Legal Pool Blockers

Live Draft Room remains mock/scouting mode until:

- dropped/released veteran source is supplied after Roster Declaration Day;
- final legal draftable pool is built;
- active legal free-agent/manual draftable files are complete or intentionally empty;
- protected roster source is confirmed for legal exclusion checks.

The page does not infer legal draftability from missing dropped-player files.

## Tests Run

Focused tests:

- `tests/test_live_draft_room_page.py`
- `tests/test_draft_prep_page.py`
- `tests/test_draft_ux_acceptance.py`

Static checks:

- `py_compile` on Draft Prep, Live Draft Room, and navigation.
- `ruff` on touched page/test files.

Browser smoke:

- `/draft-room`
- `/live-draft-room`

## Remaining Issues

- Live Draft Room is still mock/scouting mode because the final legal draft pool is not complete.
- The board uses scouting prep rows as session-only mock candidates until legal sources arrive.
- A final draft-day acceptance pass is still required after dropped/released veterans are imported.

## Next Recommended Task

Run a human/mobile review of Live Draft Room, then tighten mobile density and draft-grid ergonomics before using it on draft day.
