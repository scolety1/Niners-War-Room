# Player Stats Sidecar Contract

Verdict: `YELLOW_PLAYER_STATS_SIDECAR_CONTRACT_DEFINED_NO_BUILD`

## Scope

The future `NFLVerse Player Stats Sidecar Builder V1` may build a reproducible review-only sidecar from tracked safe NFLVerse `player_stats` data if source manifests exist. The current tracked template has schema shape but `0` row-level player_stats sidecar rows, so this plan does not claim overlap has been computed.

## Required Outputs

- `player_stats_sidecar_rows.csv`
- `player_stats_sidecar_schema_manifest.md`
- `player_stats_sidecar_coverage_report.md`
- `identity_overlap_report.md`
- `sidecar_missingness_and_censoring_report.md`
- `non_label_truth_report.md`

## Required Row Fields

- `player_id`
- `gsis_id`
- `source_player_id`
- `season`
- `week`
- `game_id`
- `team`
- `opponent`
- `position`
- `stat_name`
- `stat_value`
- `source_snapshot_id`
- `source_extraction_timestamp`
- `feature_as_of_timestamp`
- `identity_status`
- `censoring_status`
- `missingness_reason`
- `sidecar_review_allowed`
- `label_truth_allowed`
- `model_use_allowed`
- `training_allowed`
- `source_truth_allowed`

## Sidecar Rules

- `sidecar_review_allowed` may be true only for rows passing source, identity, and schema checks.
- `label_truth_allowed=false` for every row.
- `model_use_allowed=false` for every row.
- `training_allowed=false` for every row.
- `source_truth_allowed=false` for every row.
- Missing sidecar rows are `Not enough information`.
- Missing stats are not zero production.
- Incomplete windows are censored, not misses.
- Existing Outcome and Rookie labels are evaluation targets only, never input features.

## Coverage Reporting

The sidecar builder must report row counts by:

- season;
- week;
- position;
- team;
- stat family;
- identity status;
- source snapshot;
- censoring status;
- missingness reason.

## Approval Boundary

This sidecar is a review substrate only. It cannot create probabilities, alter labels, promote label truth, train models, tune models, update source truth, or wire app behavior.
