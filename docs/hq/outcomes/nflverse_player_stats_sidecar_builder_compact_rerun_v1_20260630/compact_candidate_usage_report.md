# Compact Candidate Usage Report

## Candidate Consumed

`docs/hq/data_sources/nflverse_player_stats_compact_sidecar_derivation_runner_v1_20260630/compact_player_stats_sidecar_candidate.csv`

Rows consumed: `13,628`

Rows emitted into official sidecar artifact: `13,628`

## Mapping

- `sidecar_candidate_row_id` -> `sidecar_row_id`
- `stat_name` -> `raw_stat_name`
- `stat_value` -> `raw_stat_value`
- `stat_name` -> `normalized_stat_name`
- `stat_value` -> `normalized_stat_value`
- tracked compact candidate path -> `source_artifact`

No raw local snapshot path is used as a runtime dependency in the official sidecar artifact.

## Required Candidate Filters

All emitted rows satisfy:

- `sidecar_review_allowed=true`
- `identity_join_status=SAFE_NOW_DISPLAY_ONLY`
- `review_required=false`
- `label_truth_allowed=false`
- `model_use_allowed=false`
- `training_allowed=false`
- `source_truth_allowed=false`

## Quarantined Fields

The compact derivation excludes all 12 quarantined fields:

`air_yards_share, fantasy_points, fantasy_points_ppr, headshot_url, pacr, passing_cpoe, passing_epa, racr, receiving_epa, rushing_epa, target_share, wopr`

The official sidecar artifact includes only:

- `passing_first_downs`
- `receiving_first_downs`
- `rushing_first_downs`
