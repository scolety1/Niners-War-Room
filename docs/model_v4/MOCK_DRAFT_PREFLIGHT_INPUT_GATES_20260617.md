# Mock Draft Preflight Input Gates - 2026-06-17

## Scope
The preflight gate runner checks future user-filled inputs staged under:

`local_exports/mock_draft/user_supplied_inputs_20260617/`

It is review-only. It does not run a full simulation, wire the app, promote artifacts, import real market data, or create numeric NWR scores.

## Required Gates
- `post_drop_rosters.csv` must exist and pass schema/header checks.
- `post_drop_draft_order.csv` must exist and pass schema/header checks.
- `team_managers.csv` must exist and pass schema/header checks.
- Roster coverage must prove the 10-team league context before full simulation.
- Draft order must exclude placeholder `1.00` rows and preserve review flags.

## Optional Inputs
- `dropped_veterans.csv`
- `behavior_only_adp_market.csv`
- `nwr_veteran_value_guidance.csv`

Missing optional inputs stay YELLOW/review-required. They do not become NWR value and do not authorize a full simulation by themselves.

## Output
The runner writes local-only artifacts under:

`local_exports/mock_draft/preflight_input_gates_20260617/`

Expected files:
- `mock_draft_preflight_input_gate_rows.csv`
- `mock_draft_preflight_input_gate_manifest.json`

## Guardrails
- ADP/market remains behavior-only.
- NWR value/guidance remains separate from market cost.
- Rookie board order and guidance remain read-only.
- No app, production ranking, hidden sort key, promoted artifact, Rookie HQ, Outcome HQ, or Drop Decision HQ files are touched.
- Full simulation remains blocked until all required preflight gates are GREEN.
