# Sidecar Builder Handoff

## Status

`SIDE_CAR_SOURCE_RECEIPT_READY_REVIEW_ONLY`

The previous blocker `NO_ROW_LEVEL_SOURCE` is resolved for the limited local snapshot recorded by this packet. A future sidecar builder may consume the tracked receipt and, through an explicitly approved runner/local snapshot gate, read the local-only source rows referenced by the receipt.

## Required Inputs For Future Builder

- `player_stats_row_level_receipt.csv`
- `player_stats_schema_manifest.csv`
- local snapshot root: `C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\player_stats_source_admission_v1_20260630`
- metadata file: `C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\player_stats_source_admission_v1_20260630\snapshot_metadata.json`

## Required Filters

- Use only receipt rows where `review_use_allowed=true` and `sidecar_builder_allowed=true`.
- Keep `label_truth_allowed=false`.
- Keep `model_use_allowed=false`.
- Keep `training_allowed=false`.
- Keep `source_truth_allowed=false`.
- Do not use quarantined fields unless a later source-policy lane approves them.
- Do not treat missing stats as zero unless an explicit source row records zero.

## Remaining Caveats

- Coverage is limited to the runner-requested seasons `2024-2025`.
- Source extraction timestamp exists, but source as-of/publication timestamp remains `Not enough information`.
- This packet does not approve historical replay or model experiments.
