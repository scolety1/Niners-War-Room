# Mock Draft Review-Only Readiness Status - 2026-06-16

## Branch and commit stack
- Branch: `work/mock-draft-simulator`
- `43c3148` - Build review-only mock draft simulator baseline
- `e0280f4` - Build review-only mock draft run report layer
- `5b82c1f` - Build review-only mock draft room kit
- `95f960a` - Build review-only full pool overlay

## Mission
Mock Draft HQ is a review-only drop-day prep lane for rehearsing the LVE rookie/veteran draft pool. It combines frozen Rookie HQ final manual draft guidance with LVE 061326 declared drops and available free agents, while keeping all outputs local-only and outside app/production surfaces.

## Inputs used
- LVE 061326 snapshot-derived roster, pick, free-agent, and declared-drop files under `local_exports/mock_draft_simulator/input_snapshots/lve_rosters_061326/`.
- Frozen Rookie HQ final manual draft kit imported as local-only review input under `local_exports/mock_draft/review_inputs/rookie_final_manual_kit_20260615/`.
- Declared drops preserve Brock Purdy twice as unresolved input.
- Future `1.00` placeholder picks remain excluded from simulator-ready rows.

## Local-only artifacts
- Combined simulator state: `local_exports/mock_draft/combined_simulator_state_20260616/`
- Mock draft run/report: `local_exports/mock_draft/mock_draft_run_20260616/`
- Draft-room usability kit: `local_exports/mock_draft/draft_room_kit_20260616/`
- Full-pool visibility overlay: `local_exports/mock_draft/full_pool_visibility_overlay_20260616/`

All artifact directories are ignored local exports and are not committed.

## Key counts
- Available pool rows: 141
- Frozen rookies: 54
- Declared drops: 10
- Free agents: 77
- Simulator-ready 2026 pick rows: 51
- Tim pick windows: 10
- Tim shortlist rows: 80
- Full overlay rows: 1,229
- Value-neutral overlay rows: 870

Overlay counts are window-level visibility rows, not unique-player counts.

## Current GREEN items
- Review-only services and tests are committed.
- No Streamlit/app wiring was added.
- No production ranking, sorting, hidden sort key, or app-facing output changed.
- No Rookie HQ, Outcome HQ, or Drop Decision HQ contamination.
- `local_exports/` artifacts remain ignored and uncommitted.
- Focused mock-draft tests and Ruff are passing.
- Draft-room kit and overlay make Tim/Niners pick windows usable from local CSVs.

## Current YELLOW items
- Opponent behavior is still deterministic placeholder behavior because no real ADP/market timing input has been supplied.
- Brock Purdy duplicate drop declaration remains unresolved and review-required.
- Future `1.00` placeholder picks remain review-required and excluded from simulator-ready draft rows.
- Snapshot-only veterans and free agents remain value-neutral.

## Current RED items
- None identified.

## Contamination guardrails
- ADP/market is behavior-only for opponent timing, likely pick timing, and availability.
- ADP/market must not enter, alter, blend with, backfill, sort, or impute NWR private value or rookie guidance.
- No numeric NWR score is invented from rookie rank, tier, action, snapshot rank, ADP, or market data.
- Frozen rookie guidance is copied read-only from the imported final manual kit.
- Value-neutral declared drops and free agents are visible in separate overlay sections and are not ranked against frozen rookies as NWR quality.
- Tim/Niners picks remain manual-review windows; no auto-final best pick is created.

## Recommended next steps
- Define an optional ADP/market timing input contract for opponent behavior only.
- Add optional scenario variants that remain behavior-only and do not alter NWR guidance/value.
- Manually resolve the Brock Purdy duplicate drop declaration.
- Use the local draft-room kit and full-pool overlay CSVs for draft-day review.
