# Live Draft Room Page Plan - 2026-06-09

## 1. Page Purpose

Live Draft Room is the future draft-day surface for tracking the actual offline league draft or a saved mock draft in real time.

It should answer:

- What pick is on the clock?
- Who owns the current and upcoming picks?
- Which players have already been selected?
- Who is still available in the legal/scouting pool?
- What are my upcoming picks?
- What local mock/live state can be saved, loaded, duplicated, reset, or exported?

This page is operational state tracking. It must stay separate from Draft Prep, which is planning and review.

## 2. What Stays In Draft Prep

Draft Prep remains the planning page:

- Pick-card planning for `2026 1.03`, `2026 1.04`, `2026 2.04`, `2026 2.08`, and `2026 5.04`.
- Scouting pool review using `local_exports/model_v4/draft_prep/latest/scouting_prep_pool_review_rows.csv`.
- Source readiness cards that explain legal pool status.
- Conservative candidate windows such as `In Range`, `Value If Falls`, `Needs Scouting`, `Source Limited`, `Manual Watchlist`, and `No Baseline`.
- League history context as display-only information.
- Advanced audit receipts as collapsed secondary context.

Draft Prep should not mutate mock/live draft state.

## 3. What Moves To Live Draft Room

The following belongs on the separate Live Draft Room page:

- 50-pick grid.
- Current pick / on-clock indicator.
- Team and pick-owner labels.
- Mark player drafted.
- Undo drafted pick.
- Replace pick.
- Hide drafted players.
- Best remaining board.
- Best remaining by position.
- My upcoming picks.
- Recent picks.
- Save/load mock drafts.
- Duplicate mock draft.
- Reset mock draft.
- Download current draft board / remaining pool CSVs.

These controls should no longer be first-screen content on Draft Prep.

## 4. Existing Services / Components To Reuse

Reuse the existing draft state and UX machinery rather than rebuilding it:

- `app/components/draft_session.py`
- `src/services/draft_service.py`
- `src/services/draft_state_service.py`
- `src/services/draft_ux_service.py`
- `src/services/real_draft_pool_preview_service.py`
- `src/services/mock_draft_storage_service.py`

Useful existing behavior:

- `create_empty_draft_state`
- `mark_player_drafted`
- `replace_drafted_player_at_pick`
- `undo_pick`
- `reset_mock`
- `draft_pick_grid_cells`
- `current_draft_pick`
- `is_my_turn`
- `best_option_rows_at_pick`
- `best_remaining_by_position`
- `recent_drafted_players`
- `search_available_players`
- `save_mock_draft`
- `load_mock_draft`
- `duplicate_mock_draft`
- `clear_mock_draft`

## 5. Required Data Inputs

Required now:

- Active data pack future picks, especially `fact_future_picks.csv`.
- Scouting/prep pool or draft UX ranking rows.
- Active team metadata for pick-owner labels.
- Local mock draft storage root.

Required before treating the page as legal draft-day ready:

- Final legal draftable pool.
- Dropped/released veteran source after Roster Declaration Day.
- Protected roster / unavailable-player source.
- Manual draftable additions, if any.
- Any final legal free-agent/available-player source.

Until those legal sources exist, the page must show a clear `Legal Pool Pending` state and label player availability as scouting/prep context where appropriate.

## 6. Draft State Storage Rules

Draft state must be separate from source data:

- Store active mock/live state in Streamlit session state while the app is open.
- Save named mock drafts only through local mock draft storage.
- Never write draft picks or drafted-player state back into active data packs.
- Never mutate `local_exports/data_packs/...` source files.
- Exports are backups/snapshots, not source-of-truth data pack mutations.
- Reset/clear actions must require explicit confirmation.

State should include:

- Drafted player per overall pick.
- Current pick.
- Selected pick.
- Drafted player replacement history if supported.
- Mock name and saved path metadata.
- Active data pack identifier and fingerprint to prevent loading stale mocks into incompatible pools.

## 7. Guardrails

Live Draft Room must follow these guardrails:

- Do not tune formulas.
- Do not create final draft recommendations.
- Do not use command language such as `Draft this player`, `Target`, `Buy`, `Sell`, `Cut`, or `Defer`.
- Do not invent legal draftable status.
- Do not invent a baseline for `2026 5.04`.
- Do not use market rank, league rank, ADP, startup, projections, consensus, public ranks, trade calculators, RotoWire projections/rankings, prior draft history, spreadsheet highlights, or legacy active-pack scores as private model value.
- Market, league, prior draft history, and spreadsheet highlights remain display-only context.
- Draft state must not mutate active data packs.
- Decision Board remains untouched.

Recommended UI language:

- `Best Remaining`
- `Review Candidate`
- `Scouting Only`
- `Legal Pool Pending`
- `Needs Scouting`
- `Source Limited`
- `No Baseline`
- `Manual Watchlist`

## 8. UI Layout Sketch

Top band:

- Page title: `Live Draft Room`
- Status banner:
  - `Legal Pool Pending` if dropped/released veterans are not supplied.
  - `Live/mock state is local and does not modify source data.`
- Current pick card:
  - Pick label.
  - Overall pick.
  - Current owner.
  - On-clock indicator.
  - My-turn flag.

Main layout:

- Left / top on mobile:
  - 50-pick grid.
  - Current pick highlighted.
  - My picks highlighted.
  - Drafted picks visually marked.

- Right / below on mobile:
  - Search / assign player.
  - Selected pick status.
  - Replace/mark selected player.
  - Undo last pick.
  - Reset mock with confirmation.

Secondary sections:

- Best Remaining board.
- Best Remaining by Position.
- My Upcoming Picks.
- Recent Picks.

Collapsed utility sections:

- Save / Load / Duplicate Mock.
- Draft Backups / CSV downloads.
- Advanced state and source details.

Mobile behavior:

- Current pick and search should appear before large tables.
- Pick grid should be compact and horizontally safe.
- Best remaining board can use a scrollable dataframe.
- Save/load controls should stay collapsed on phones unless opened.

## 9. Test Plan

Unit/readback tests:

- Live Draft Room page title exists.
- Draft Prep no longer contains first-screen mock/live controls.
- Live Draft Room imports/reuses existing draft session/state services.
- Draft state writes only to session/local mock storage, not active data packs.
- Reset/clear actions require confirmation.
- `2026 5.04` remains no-baseline if shown.
- Legal pool pending state appears when dropped-player source is missing.
- Best remaining hides drafted players.
- Mark drafted advances current pick.
- Undo restores the last drafted player to availability.
- Replace pick changes only the selected mock/live state.
- Save/load/duplicate mock round-trips via local mock storage.
- Decision Board is untouched.
- No forbidden recommendation language appears.

Browser smoke:

- Desktop and mobile page load.
- Current pick/on-clock indicator visible.
- Pick grid usable.
- Search/assign controls usable.
- Save/load controls collapsed by default.
- No console errors.

## 10. Open Blockers Before Implementation

- Final legal draftable pool is not complete.
- Dropped/released veteran source is missing until Roster Declaration Day.
- Active legal free-agent/manual draftable files are incomplete or missing.
- Need a product decision on whether Live Draft Room should default to legal-only rows or allow scouting-only rows while legal pool is pending.
- Need a product decision on the visible route:
  - keep `/draft-room` for Draft Prep legacy compatibility and use `/live-draft-room` for the new page, or
  - eventually move Draft Prep to `/draft-prep` and reserve `/draft-room` for the live tool.
- Need a mobile layout pass before draft-day use.

## Recommended Implementation Sequence

1. Add a hidden or visible `Live Draft Room` page shell using existing state services.
2. Move the old mock/live UI from Draft Prep into the new page with minimal behavior changes.
3. Add legal-pool pending banner and source readiness cards.
4. Run existing draft state and mock storage tests.
5. Browser-smoke desktop and mobile.
6. Only after dropped/released veteran sources arrive, run a legal-pool acceptance pass.
