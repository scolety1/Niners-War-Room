# Model v4.6 Evidence Risk Export Consolidation

## Goal

Patch the non-blocking v4.5 audit concern that Evidence Risk raw exports can look duplicated when a player has multiple module/context rows.

## Changes

- Preserved `source_risk_player_rows.csv` as the module/context-level audit export.
- Added `source_risk_player_summary_rows.csv` as a one-row-per-player human review export.
- Updated `SOURCE_RISK_HEATMAP.md` to explain why duplicate names can appear in raw module rows.
- Added tests proving summary rows are unique by player while raw rows remain available.

## New Summary Export

Path:

`local_exports/model_v4/source_risk_heatmap/latest/source_risk_player_summary_rows.csv`

Columns:

- `player_name`
- `position`
- `model_score`
- `worst_source_risk_level`
- `evidence_modules_present`
- `evidence_modules_missing_or_partial`
- `biggest_source_risk`
- `warning_summary`
- `raw_module_row_count`
- `allowed_use`
- `blocked_use`
- `formula_version`

## Safety

This patch does not change formulas, rankings, scores, active app state, My Team, War Board, readiness gates, or app promotion. Missing evidence remains missing. The new summary export is review-only and exists only to make Evidence Risk easier to inspect.
