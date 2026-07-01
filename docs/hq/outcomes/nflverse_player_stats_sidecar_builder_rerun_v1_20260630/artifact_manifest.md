# NFLVerse Player Stats Sidecar Builder Rerun V1 Artifact Manifest

Verdict: `YELLOW_PLAYER_STATS_SIDECAR_BLOCKED_NEEDS_DERIVATION_RUNNER`

Branch: `work/nflverse-player-stats-sidecar-builder-rerun-v1-20260630`

Base HQ HEAD: `d93dd0ddbcb6539cad4d59aaab408349a633b64a`

Packet path:
`docs/hq/outcomes/nflverse_player_stats_sidecar_builder_rerun_v1_20260630/`

## Purpose

This packet reruns the NFLVerse Player Stats Sidecar Builder V1 after row-level source admission landed GREEN.

The row-level source blocker is resolved for review-only admission receipts, but compact sidecar derivation is still blocked because no approved sidecar derivation runner/service exists in the repo.

## Files

- `artifact_manifest.md`
- `player_stats_sidecar_rerun_summary.md`
- `player_stats_sidecar_schema.csv`
- `player_stats_sidecar_coverage_matrix.csv`
- `blocked_sidecar_rerun_report.md`
- `source_admission_receipt_usage.md`
- `label_truth_guardrail_report.md`
- `next_gate_recommendations.md`
- `merge_safety_report.md`

`player_stats_sidecar_artifact.csv` is not created because no approved compact derivation runner exists. Creating rows directly from raw local snapshot files would bypass the requested derivation gate.

## Primary Inputs

- `docs/hq/data_sources/nflverse_player_stats_row_level_source_admission_v1_20260630/`
- `docs/hq/outcomes/nflverse_experiment_substrate_build_plan_v1_20260630/player_stats_sidecar_contract.md`
- `docs/hq/outcomes/nflverse_player_stats_sidecar_builder_v1_20260630/`
- `docs/hq/outcomes/nflverse_player_stats_sidecar_overlap_v1_20260630/`
- `docs/hq/outcomes/nflverse_label_parity_outcome_sidecar_evidence_v1_20260630/`
- `docs/hq/data_sources/nflverse_dataset_level_refresh_health_20260630/`
- `docs/hq/data_sources/nflverse_player_context_display_20260630/`
- existing Outcome V2 label/source docs

## Non-Activation Statement

This packet does not promote label truth, train models, run experiments, create probabilities, approve model/training/source-truth use, or wire app behavior.
