# NFLVerse Player Stats Compact Sidecar Derivation Runner V1 Manifest

- verdict: `GREEN_COMPACT_SIDECAR_DERIVATION_READY_REVIEW_ONLY`
- service: `src/services/nflverse_player_stats_compact_sidecar_derivation_service.py`
- receipt_input: `C:\NWR\Niners-War-Room-nflverse-player-stats-compact-sidecar-derivation-runner-v1-20260630\docs\hq\data_sources\nflverse_player_stats_row_level_source_admission_v1_20260630\player_stats_row_level_receipt.csv`
- schema_input: `C:\NWR\Niners-War-Room-nflverse-player-stats-compact-sidecar-derivation-runner-v1-20260630\docs\hq\data_sources\nflverse_player_stats_row_level_source_admission_v1_20260630\player_stats_schema_manifest.csv`
- identity_input: `C:\NWR\Niners-War-Room-nflverse-player-stats-compact-sidecar-derivation-runner-v1-20260630\docs\hq\data_sources\nflverse_player_context_display_20260630\nflverse_player_context_display_artifact.csv`
- raw_source_tracked_in_git: `false`
- compact_candidate_rows: `13628`
- receipts_validated: `2`
- label_truth_allowed: `false`
- model_use_allowed: `false`
- training_allowed: `false`
- source_truth_allowed: `false`

## Outputs

- `compact_player_stats_sidecar_candidate.csv`
- `compact_player_stats_sidecar_schema.csv`
- `derivation_coverage_matrix.csv`
- `quarantined_fields_report.md`
- `source_receipt_validation_report.md`
- `sidecar_builder_handoff.md`
- `merge_safety_report.md`
