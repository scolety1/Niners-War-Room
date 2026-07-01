# Source Admission Receipt Usage

## Admission Packet

Input:
`docs/hq/data_sources/nflverse_player_stats_row_level_source_admission_v1_20260630/`

Verdict:
`GREEN_PLAYER_STATS_ROW_LEVEL_SOURCE_ADMITTED_REVIEW_ONLY`

## Receipt Rows

The tracked receipt has two admitted rows:

1. `player_stats_weekly__player_stats_source_admission_v1_20260630`
2. `player_stats_seasonal__player_stats_source_admission_v1_20260630`

Both rows have:

- `review_use_allowed=true`
- `sidecar_builder_allowed=true`
- `label_truth_allowed=false`
- `model_use_allowed=false`
- `training_allowed=false`
- `source_truth_allowed=false`

## Source Snapshot

The admitted source rows point to a local-only snapshot:

`C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\player_stats_source_admission_v1_20260630`

The snapshot was produced by `scripts/run_nflverse_refresh_v0.ps1`, which calls `scripts/nflverse_scheduled_pull_v0.py`.

## How The Receipt Was Used Here

This rerun uses the tracked receipt for coverage and policy reporting only. It does not read the local raw snapshot directly and does not generate compact sidecar rows.

## Quarantined Fields

The admitted receipt and schema identify 12 quarantined fields:

- `air_yards_share`
- `fantasy_points`
- `fantasy_points_ppr`
- `headshot_url`
- `pacr`
- `passing_cpoe`
- `passing_epa`
- `racr`
- `receiving_epa`
- `rushing_epa`
- `target_share`
- `wopr`

No sidecar rows were created, and no quarantined field is used by this packet.

## Source-As-Of Caveat

The admission packet records `source_asof_timestamp=Not enough information`. That remains a blocker for replay, model, training, and label-truth use.
