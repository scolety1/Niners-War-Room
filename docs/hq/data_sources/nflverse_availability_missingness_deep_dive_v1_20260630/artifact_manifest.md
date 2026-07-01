# NFLVerse Availability Missingness Deep-Dive Manifest

- artifact: `nflverse_availability_missingness_deep_dive_v1_20260630`
- verdict: `YELLOW_AVAILABILITY_DEEP_DIVE_READY_HEALTH_INFERENCE_BLOCKED`
- branch: `work/nflverse-availability-missingness-deep-dive-v1-20260630`
- worktree: `C:\NWR\Niners-War-Room-nflverse-availability-missingness-deep-dive-v1-20260630`
- base_head: `9dafea81b3316a02f8a051762b9d53dc84791fc7`
- scope: evidence and audit only
- app_behavior_changed: `false`
- model_rank_source_truth_changed: `false`
- availability_denominator_artifact_rebuilt: `false`
- player_context_artifact_rebuilt: `false`

## Inputs

- `docs/hq/outcomes/nflverse_model_candidate_readiness_matrix_v1_20260630/`
- `docs/hq/data_sources/nflverse_availability_denominator_missingness_evidence_v1_20260630/`
- `docs/hq/data_sources/nflverse_availability_denominator_display_v1_20260630/`
- `docs/hq/injury_availability_context/injury_availability_display_context_safe_upgrade_20260630/`
- `docs/hq/data_sources/nflverse_player_context_display_20260630/`

## Outputs

- `artifact_manifest.md`
- `availability_missingness_deep_dive_summary.md`
- `availability_field_deep_dive_matrix.csv`
- `games_missed_feasibility_report.md`
- `censoring_policy.md`
- `health_inference_blocker_report.md`
- `next_gate_recommendations.md`
- `merge_safety_report.md`

## Non-Approval Statement

This packet does not approve injury risk, durability scoring, medical projection,
health inference, model input, training input, source truth, rank logic, hidden
sort, recommendations, trade value, pick value, or app behavior.
