# Mock Draft User-Filled Input Staging Contract - 2026-06-17

## Scope
Future Tim-filled mock draft inputs must be staged locally under:

`local_exports/mock_draft/user_supplied_inputs_20260617/`

These files are review inputs only. They are not promoted artifacts, app inputs, production rankings, or Rookie/Outcome/Drop Decision HQ files.

## Required Future Filenames
- `post_drop_rosters.csv`
- `post_drop_draft_order.csv`
- `team_managers.csv`

## Optional Future Filenames
- `dropped_veterans.csv`
- `behavior_only_adp_market.csv`
- `nwr_veteran_value_guidance.csv`

## Validation Before Simulation
- Schema/header validation must pass for required files.
- Roster coverage must show all 10 teams.
- Draft order validation must confirm pick labels, owners, and placeholder exclusions.
- Missing optional files remain YELLOW/review-required, not RED.
- Full simulation remains blocked until all required gates are GREEN.

## ADP/Market Rule
Real ADP/market, if supplied later, may only pass through the behavior-only contract. It can affect opponent behavior, availability pressure, and likely pick timing. It must not become NWR private value or rookie guidance.

## NWR Veteran Guidance Rule
NWR veteran/free-agent guidance, if supplied later, must be explicitly approved and separate from ADP/market. It must not be inferred from market cost.

## Local-Only Handling
- Filled files stay under `local_exports/` and must not be committed unless Tim explicitly approves.
- No full simulation should run from staged files until preflight gates pass.
- No numeric NWR score may be invented by staging, validation, inventory, or preflight checks.

## Verdict
GREEN as a staging contract. Full simulation remains YELLOW/blocked until required staged files are supplied and validated.
