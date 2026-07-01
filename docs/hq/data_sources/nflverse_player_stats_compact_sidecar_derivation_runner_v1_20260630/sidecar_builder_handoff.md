# Sidecar Builder Handoff

Status: `COMPACT_SIDECAR_CANDIDATE_READY_REVIEW_ONLY`

Future sidecar builder lanes may consume:

- `compact_player_stats_sidecar_candidate.csv`
- `compact_player_stats_sidecar_schema.csv`
- `derivation_coverage_matrix.csv`

Required filters:

- `sidecar_review_allowed=true`
- `identity_join_status=SAFE_NOW_DISPLAY_ONLY`
- `review_required=false`
- `label_truth_allowed=false`
- `model_use_allowed=false`
- `training_allowed=false`
- `source_truth_allowed=false`

Source receipt SHA used for weekly candidates: `a38c47ea830e6929e8de31d822496862d13873d13689ff90d2e50dac854901ba`.

Absence from the compact candidate file is not zero production. V1 emits
explicit nonzero first-down stats only.
