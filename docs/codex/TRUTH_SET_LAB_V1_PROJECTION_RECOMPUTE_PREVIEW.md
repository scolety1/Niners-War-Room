# Truth Set Lab v1 Projection Recompute Preview

## Files

- Source input: `local_exports/truth_set_lab/v1/source_clean/projections.csv`
- Preview output: `local_exports/truth_set_lab/v1/reports/projection_recompute_preview.csv`
- Flags: `local_exports/truth_set_lab/v1/reports/projection_recompute_flags.csv`
- Summary: `local_exports/truth_set_lab/v1/reports/projection_recompute_summary.json`
- Separate first-down estimator preview:
  `local_exports/truth_set_lab/v1/reports/first_down_projection_estimator_preview.csv`

## Result

Status: preview only. No model scores changed.

The recompute layer ignores the supplied `projected_lve_points_if_calculable` column and recalculates LVE projection points from the projected stat columns using:

- Passing yards: `0.04`
- Passing TD: `3`
- Interception: `-2`
- Rushing/receiving yards: `0.10`
- Rushing/receiving TD: `4`
- Rushing/receiving first down: `0.40` when directly present
- No PPR

## Summary

- Rows processed: 40
- Offensive projection rows: 37
- Missing offensive projection rows: 3
- Supplied points rejected as non-LVE: 36
- Direct first-down projection rows: 0
- Estimable but missing first-down rows: 37
- Fully missing first-down rows: 3
- Projection team-mismatch rows: 3
- High-active-value missing-projection rows: 0

## Source Quality Flags

The preview now carries `projection_source_quality_status` and
`projection_source_quality_flags` on each row. These are audit flags only; they do
not promote projection rows into active scoring.

Current statuses:

- `missing_first_down_projection`: rows with offensive projection stats but no
  projected rushing/receiving first downs.
- `missing_projection`: rows without a usable offensive projection line.
- `team_mismatch`: projection NFL team does not match the active model reference
  team.
- `review_needed`: reserved for combined or high-impact projection quality issues.
- `clean`: no current projection quality flag.

Current team mismatches:

- David Montgomery: projection `HOU`, active model `DET`
- Romeo Doubs: projection `NE`, active model `GB`
- Wan'Dale Robinson: projection `TEN`, active model `NYG`

## Policy

Use `recomputed_lve_points` only as preview evidence until import gates approve it. The supplied projection points remain audit-only because they materially differ from no-PPR LVE scoring. First-down projections remain a source gap for this file.

## First-Down Estimator Design

A separate preview-only estimator now exists for missing rushing/receiving
first-down projections. It derives broad position-level first-down rates from
local nflverse weekly player stats and writes estimated first-down points to a
separate report. These estimates are not used by active scoring or the projection
recompute output.

See `docs/codex/TRUTH_SET_LAB_V1_FIRST_DOWN_PROJECTION_ESTIMATOR_DESIGN.md`.
