# Model v4 Receipt Recovery Search Plan

## Search Rule

This plan does not authorize broad discovery, raw import, or regeneration. A future recovery lane should search only approved local/recovered artifact locations and tracked docs already identified by prior lanes.

## Priority 1: Checkpoint And Component Rows

Expected file names:

- `current_value_full_board_review_rows.csv`
- `current_player_value_full_board_review_rows.csv`
- `full_player_board_value_review_rows.csv`
- `component_rows.csv`
- `component_receipts.csv`
- `current_value_review_rows.csv`

Expected columns:

- player identity key: `player_id`, `nwr_player_id`, `gsis_id`, or documented bridge
- `player_name`
- `position`
- `feature_season` or frozen as-of date
- `checkpoint_review_score`
- `position_specific_review_score`
- `nwr_dynasty_score`
- component name/value fields
- source receipt or provenance fields

Search locations:

- `C:\NWR\_manual_recovery_dropzone\current_board_rebuild_inputs_v1\`
- recovered vacation repo `local_exports\model_v4\current_value\latest\`
- recovered candidate folders under `local_exports\model_v4\current_value\candidate*\`
- timestamped data pack `model_outputs` folders
- prior Model v4 lane worktrees under `C:\NWR\Niners-War-Room-model-v4-*`

Validation checks:

- file exists
- row count recorded
- column count recorded
- schema captured
- SHA256 hash captured
- feature season/as-of date available
- no target season label columns used as input
- no current-only context backfilled into history

## Priority 2: Lifecycle, Age, Role, Confidence

Expected file names:

- `lifecycle_age_receipts.csv`
- `veteran_player_inputs.csv`
- `source_coverage_matrix.csv`
- `component_receipts.csv`
- `review_safe_qb_age_adapter_from_lifecycle_receipts.csv`

Expected columns:

- player identity key
- feature season or as-of date
- age or birth-date-derived age
- lifecycle bucket
- role or archetype
- confidence cap/status
- source coverage flags

Validation checks:

- age is computed from feature-season date, not current date
- missingness caps are explicit
- role context is lagged or feature-season final, not target-season current
- confidence flags are not treated as production truth

## Priority 3: WR/QB V2 Candidate Overlay

Expected file names:

- `candidate_board*.csv`
- `pre_wr_qb_v2*.csv`
- `post_wr_qb_v2*.csv`
- `old_pocket_qb*.csv`
- candidate overlay receipt or decision files

Validation checks:

- overlay input row preserved
- overlay output row preserved
- reason/decision column present
- historical feature season available
- no name-only identity joins
- no current-season player status used historically

## Priority 4: Route, Red-Zone, Return, Shadow

Expected file names:

- route denominator receipts if admitted by Route Recovery
- red-zone source admission receipts
- `shadow_model_v2_metrics.csv`
- full scoring sidecar or direct return field receipts

Validation checks:

- source admission status is not blocked
- licensing status is explicit
- identity status is safe
- missing values are not converted to zero
- direct return fields are not replaced with ambiguous special teams fields

## Stop Conditions

Stop and report rather than recover/regenerate if:

- file provenance is unclear
- file is only in unapproved raw/shared/local cache
- hash cannot be captured
- feature-season as-of cannot be proven
- identity joins rely on names only
- recovered rows include target-season outcomes as input fields
- any regeneration would require formula tuning, tournament execution, app behavior, ranking behavior, or source promotion
