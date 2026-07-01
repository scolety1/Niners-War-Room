# NFLVerse Label Parity Validator V1 Artifact Manifest

Verdict: `YELLOW_LABEL_PARITY_PARTIAL_ROW_LEVEL_BLOCKERS`

Branch: `work/nflverse-label-parity-validator-v1-20260630`

Base HQ HEAD: `7fcc34c02fd19b586c93adfe8554701dd92c8436`

Packet path:
`docs/hq/outcomes/nflverse_label_parity_validator_v1_20260630/`

## Purpose

This packet validates the review-only NFLVerse player_stats sidecar against existing Outcome label families where feasible, without promoting label truth.

## Files

- `artifact_manifest.md`
- `label_parity_validator_summary.md`
- `label_parity_matrix.csv`
- `sidecar_label_overlap_matrix.csv`
- `unmatched_sidecar_rows_summary.md`
- `unmatched_label_rows_summary.md`
- `first_down_parity_report.md`
- `label_truth_guardrail_report.md`
- `next_gate_recommendations.md`
- `merge_safety_report.md`

## Primary Sidecar Input

`docs/hq/outcomes/nflverse_player_stats_sidecar_builder_compact_rerun_v1_20260630/player_stats_sidecar_artifact.csv`

Sidecar rows: `13,628`

## Validator Result

The sidecar substrate validates as review-only input, but label parity is partial because the tracked existing Outcome V2 label artifact is field-level validation evidence, not row-level player-season labels comparable to weekly sidecar rows.

No row-level matches are fabricated.

## Non-Activation Statement

This packet does not replace label truth, train models, run experiments, create probabilities, approve model/training/source-truth use, or wire app behavior.
