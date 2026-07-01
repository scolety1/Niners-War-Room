# Merge Safety Report

Verdict: `PASS`

## Scope

This lane creates a docs/CSV evidence packet only.

## Files Created

- `docs/hq/data_sources/nflverse_availability_missingness_deep_dive_v1_20260630/artifact_manifest.md`
- `docs/hq/data_sources/nflverse_availability_missingness_deep_dive_v1_20260630/availability_missingness_deep_dive_summary.md`
- `docs/hq/data_sources/nflverse_availability_missingness_deep_dive_v1_20260630/availability_field_deep_dive_matrix.csv`
- `docs/hq/data_sources/nflverse_availability_missingness_deep_dive_v1_20260630/games_missed_feasibility_report.md`
- `docs/hq/data_sources/nflverse_availability_missingness_deep_dive_v1_20260630/censoring_policy.md`
- `docs/hq/data_sources/nflverse_availability_missingness_deep_dive_v1_20260630/health_inference_blocker_report.md`
- `docs/hq/data_sources/nflverse_availability_missingness_deep_dive_v1_20260630/next_gate_recommendations.md`
- `docs/hq/data_sources/nflverse_availability_missingness_deep_dive_v1_20260630/merge_safety_report.md`

## Confirmed Non-Mutations

- No app files changed.
- No service files changed.
- No tests changed.
- No model files changed.
- No rank files changed.
- No source-truth files changed.
- No latest pointers changed.
- No frozen board files changed.
- No Live Draft, Mock Draft, Trading Lab, trade-value, pick-value, or
  recommendation files changed.
- No tracked NFLVerse display artifacts rebuilt.
- No raw shared-data files added.

## Approval Invariants

All rows in `availability_field_deep_dive_matrix.csv` must have:

- `can_use_for_experiment_now=false`
- `can_use_for_model_now=false`
- `can_use_for_training_now=false`
- `can_use_for_source_truth_now=false`

Additional invariants:

- `games_missed_while_rostered` must have `can_display_now=false`.
- `games_missed_while_rostered` must have `can_represent_absence_safely=false`.
- No field may approve health inference.
- Missing values remain `Not enough information`.

## Validation Results

- CSV schema and approval invariant validation: `PASS`
- Fields audited: `15`
- Experiment-safe fields: `0`
- Focused injury/source tests: `28 passed`
- `git diff --check`: `PASS`
- Pending path scan: only this docs packet is changed
- Protected app/model/rank/source-truth path scan: `PASS`
- Raw/shared/vendor/Gmail/rumor path scan: `PASS`
- Forbidden active-approval scan: `PASS`

## Final Merge Posture

Safe to merge as an evidence packet if validation passes. This packet does not
activate app behavior or downstream logic.
