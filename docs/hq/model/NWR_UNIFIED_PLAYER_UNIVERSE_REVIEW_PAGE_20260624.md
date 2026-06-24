# NWR Unified Player Universe Review Page

Date: 2026-06-24

Route: `/unified-universe-review`

Scope: read-only review/debug page.

## What Changed

Added a hidden advanced Streamlit route for inspecting the consolidated unified player universe review artifact and its blocker/duplicate policy outputs.

The page is clearly labeled:

`Review-only. Not used by rankings, model, or Drafting Mode.`

## What The Page Loads

The page reads review-only artifacts from:

- `docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_consolidated_review.csv`
- `docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_remaining_blockers.csv`
- `docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_consolidation_decisions.csv`
- `docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_source_summary.csv`
- `docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_validation_report.csv`

## Current Counts

- Consolidated rows: 368
- Veterans: 240
- Rookies/prospects: 54
- PDF free agents: 74
- Blockers: 310
- Missing player_id blockers: 5
- Missing age blockers: 42
- Review-needed consolidated rows: 248
- App wiring allowed: no
- Model input allowed: no

## UI Sections

The page includes:

- Summary metrics for row counts, blocker counts, and review-only gates.
- Filters for player type, source layer, position, review status, blocker type, missing player_id, missing age, market status, outcome status, and manual review flag.
- Main review table for consolidated player rows.
- Blocker table for app-wiring blockers.
- Duplicate/consolidation decision table.
- Source summary and validation report expander.
- Download button for the filtered review table.

## Guardrails

This page:

- is for inspection only.
- does not change rankings.
- does not change model inputs.
- does not approve app wiring.
- does not wire the artifact into Dynasty Rankings, Drafting Mode, Player Compare, Trading Lab, or model logic.
- keeps market data display-only.
- keeps missing Outcome as `Not enough information`, not low probability.

## Route Placement

The route is registered as hidden advanced navigation. It is directly available at `/unified-universe-review`, but it is not added to the primary app navigation because it is a review/debug surface rather than a draft decision workflow.

## Tests

Focused tests cover:

- consolidated artifact loading.
- summary counts.
- blocker counts.
- filter behavior.
- app/model gates remaining `no`.
- missing age/player_id blocker visibility.
- duplicate/consolidation decision loading.
- route registration.
- review-only copy.

## Known Limitations

- The page does not resolve identity gaps.
- The page does not resolve missing ages.
- The page does not approve app wiring.
- The page does not make the unified universe a source for live rankings or Drafting Mode.
