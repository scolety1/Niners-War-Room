# NFLVerse Player Stats Sidecar Builder Compact Rerun V1 Artifact Manifest

Verdict: `GREEN_PLAYER_STATS_SIDECAR_BUILT_REVIEW_ONLY_FROM_COMPACT_CANDIDATE`

Branch: `work/nflverse-player-stats-sidecar-builder-compact-rerun-v1-20260630`

Base HQ HEAD: `927d0278602ed48f74341697d386528c92df119b`

Packet path:
`docs/hq/outcomes/nflverse_player_stats_sidecar_builder_compact_rerun_v1_20260630/`

## Purpose

This packet consumes the tracked compact player_stats sidecar candidate and creates the official tracked review-only NFLVerse player_stats sidecar artifact for later Label Parity Validator use.

## Files

- `artifact_manifest.md`
- `player_stats_sidecar_compact_rerun_summary.md`
- `player_stats_sidecar_artifact.csv`
- `player_stats_sidecar_schema.csv`
- `player_stats_sidecar_coverage_matrix.csv`
- `compact_candidate_usage_report.md`
- `label_truth_guardrail_report.md`
- `next_gate_recommendations.md`
- `merge_safety_report.md`

## Source Candidate

Input candidate:
`docs/hq/data_sources/nflverse_player_stats_compact_sidecar_derivation_runner_v1_20260630/compact_player_stats_sidecar_candidate.csv`

Candidate verdict:
`GREEN_COMPACT_SIDECAR_DERIVATION_READY_REVIEW_ONLY`

## Non-Activation Statement

This packet does not promote label truth, train models, run experiments, create probabilities, approve model/training/source-truth use, or wire app behavior.
