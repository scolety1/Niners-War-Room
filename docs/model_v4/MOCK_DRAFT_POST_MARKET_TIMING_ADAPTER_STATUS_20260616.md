# Mock Draft Post-Market Timing Adapter Status - 2026-06-16

## Branch and commit stack
- Branch: `work/mock-draft-simulator`
- `43c3148` - Build review-only mock draft simulator baseline
- `e0280f4` - Build review-only mock draft run report layer
- `5b82c1f` - Build review-only mock draft room kit
- `95f960a` - Build review-only full pool overlay
- `f9a020c` - Document mock draft review-only readiness status
- `b993bf8` - Document mock draft ADP market timing guardrails
- `e878a1d` - Build fake-only market timing adapter

## Mission
Mock Draft HQ is a review-only drop-day prep lane for Tim/Niners draft prep. It combines the frozen Rookie HQ final manual kit with the LVE 061326 declared drops and available free agents, while keeping all simulator, report, kit, overlay, and market-timing dry-run outputs local-only.

## Current review-only capability
- Combined simulator state joins frozen rookies, declared drops, free agents, and simulator-ready 2026 picks.
- Pick-by-pick run/report produces deterministic review rows and Tim/Niners manual-review shortlists.
- Draft-room kit produces Tim pick windows, manual shortlist rows, opponent summaries, and review-flag files.
- Full-pool visibility overlay exposes frozen rookie options separately from value-neutral declared drops/free agents.
- ADP/market timing contract defines behavior-only input rules and contamination guardrails.
- Fake-only market timing adapter validates the plumbing with synthetic fixture rows only.

## Local-only artifacts
- Combined simulator state: `local_exports/mock_draft/combined_simulator_state_20260616/`
- Mock draft run/report: `local_exports/mock_draft/mock_draft_run_20260616/`
- Draft-room usability kit: `local_exports/mock_draft/draft_room_kit_20260616/`
- Full-pool visibility overlay: `local_exports/mock_draft/full_pool_visibility_overlay_20260616/`
- Imported frozen Rookie HQ review input: `local_exports/mock_draft/review_inputs/rookie_final_manual_kit_20260615/`
- LVE 061326 extraction snapshot: `local_exports/mock_draft_simulator/input_snapshots/lve_rosters_061326/`
- Fake market timing dry run: `local_exports/mock_draft/fake_market_timing_dry_run_20260616/`

All `local_exports/` artifacts are ignored local outputs and must remain uncommitted.

## Key counts
- Available pool rows: 141
- Frozen rookies: 54
- Declared drops: 10
- Free agents: 77
- Simulator-ready 2026 picks: 51
- Tim pick windows: 10
- Tim shortlist rows: 80
- Full overlay rows: 1,229
- Fake market timing rows: 3
- Behavior-only eligible fake market rows: 2
- Contamination checks: 6 passed / 6

## Current GREEN items
- All review-only code/docs through the fake-only market timing adapter are committed.
- Focused mock-draft tests and Ruff are passing.
- Fake-only market adapter validates behavior-only plumbing without real market data.
- No Streamlit/app wiring was added.
- No production ranking, sorting, hidden sort key, or app-facing output changed.
- No Rookie HQ, Outcome HQ, or Drop Decision HQ contamination.
- `local_exports/` artifacts remain ignored and uncommitted.

## Current YELLOW items
- Real opponent behavior remains uncalibrated because no real behavior-only ADP/market timing source has been imported.
- Brock Purdy duplicate drop declaration remains unresolved and review-required.
- Future `1.00` placeholder picks remain review-required and excluded from simulator-ready rows.
- Snapshot-only veterans and free agents remain value-neutral.

## Current RED items
- None identified.

## Contamination guardrails
- ADP/market may affect only opponent behavior, likely pick timing, availability notes, and behavior-only scenario outputs.
- ADP/market must not enter NWR private quality/value.
- ADP/market must not alter frozen rookie rank, tier, draft action, warnings, notes, formulas, or board order.
- No numeric NWR score is invented from rookie rank, tier, action, snapshot rank, ADP, market data, or fake timing rows.
- Frozen rookie guidance remains copied read-only from the imported final manual kit.
- Value-neutral veterans/free agents are not ranked against frozen rookies as NWR quality.
- The fake adapter does not permit real market data promotion; it defaults to `tests/fixtures/mock_draft/fake_market_timing_rows.csv` and marks outputs as local dry-run only.

## Recommended next steps
- Optionally import a real ADP/market timing source only through the committed behavior-only contract.
- Manually review the Brock Purdy duplicate drop declaration.
- Optionally add scenario variants using behavior-only market timing, still without NWR value contamination.
- Use the local draft-room kit and full-pool overlay for manual draft prep.

## Current verdict
- GREEN for review-only infrastructure and fake timing plumbing.
- YELLOW for real opponent-behavior calibration until an approved behavior-only timing source is imported.
- RED: none.
