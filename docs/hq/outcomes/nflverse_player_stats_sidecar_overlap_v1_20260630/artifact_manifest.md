# NFLVerse Player Stats Sidecar Build/Overlap Evidence V1 Artifact Manifest

Verdict: `YELLOW_PLAYER_STATS_SIDECAR_OVERLAP_READY_NO_LABEL_PROMOTION`

Branch: `work/nflverse-player-stats-sidecar-overlap-v1-20260630`

Base HQ HEAD: `9dafea81b3316a02f8a051762b9d53dc84791fc7`

Packet path:
`docs/hq/outcomes/nflverse_player_stats_sidecar_overlap_v1_20260630/`

## Purpose

This packet audits the current tracked evidence for an NFLVerse `player_stats` sidecar overlap against existing Outcome label families.

It is sidecar evidence only. It does not replace label truth, create probabilities, train or tune models, approve model/training/source-truth use, or wire app behavior.

## Files

- `artifact_manifest.md`
- `sidecar_overlap_summary.md`
- `player_stats_sidecar_overlap_matrix.csv`
- `parity_gap_report.md`
- `label_truth_guardrail_report.md`
- `next_gate_recommendations.md`
- `merge_safety_report.md`

`unmatched_label_rows.csv` and `unmatched_nflverse_rows.csv` are not created in this packet because no tracked row-level NFLVerse player_stats sidecar exists to compute unmatched player-season rows without fabrication.

## Inputs Inspected

- `docs/hq/outcomes/nflverse_model_candidate_readiness_matrix_v1_20260630/`
- `docs/hq/outcomes/nflverse_label_parity_outcome_sidecar_evidence_v1_20260630/`
- `docs/hq/outcomes/outcome_v2_2000_validation_calibration_20260630/`
- `docs/hq/rookie_outcomes/rookie_outcomes_drafted_only_feature_policy_nflverse_green_rerun_20260630/`
- `docs/hq/data_sources/nflverse_player_context_display_20260630/`
- `templates/real_data_inputs/nflverse_stats_upgrade/nflverse_player_stats_weekly.csv`

## Source Reality

- The tracked weekly NFLVerse player_stats template has schema columns but `0` data rows.
- The tracked rookie drafted-only sidecar feasibility matrix has `52` position-season review rows.
- The feasibility matrix reports drafted-player and Outcome-label-overlap counts, but does not compute row-level NFLVerse player_stats sidecar matches.
- The prior label-parity packet keeps NFLVerse `player_stats` review-only and not label truth.

## Non-Activation Statement

All model, training, source-truth, app, rank, and active probability uses remain disallowed by this packet.
