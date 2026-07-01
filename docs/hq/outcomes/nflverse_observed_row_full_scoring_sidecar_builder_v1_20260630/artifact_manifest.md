# NFLVerse Observed-Row Full Scoring Sidecar Builder V1 - Artifact Manifest

## Verdict

`YELLOW_OBSERVED_ROW_FULL_SCORING_SIDECAR_PARTIAL_COMPONENT_BLOCKERS`

## Base

`origin/work/hq-parallel-control` at `6181e9c12bf7135b16ed5004094b9497909afeb3`.

## Source receipt

- Dataset: `player_stats_weekly`
- Raw source path: `C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\player_stats_source_admission_v1_20260630\player_stats_weekly.csv`
- Receipt SHA256: `a38c47ea830e6929e8de31d822496862d13873d13689ff90d2e50dac854901ba`
- Validated SHA256: `a38c47ea830e6929e8de31d822496862d13873d13689ff90d2e50dac854901ba`

## Compact sidecar

- Rows: `90,092`
- Nonzero component rows: `54,986`
- Explicit zero component rows: `35,106`
- Mapped observed player-week rows considered: `12,268`
- Mapped players: `232`
- Artifact SHA256: `6d0037bbe9e19b5e04e468dc9b7a6c638ae43d9a31f8ed2cee64ebdf4c31d34e`

## Files

| File | Purpose |
| --- | --- |
| `artifact_manifest.md` | Packet manifest and verdict. |
| `observed_row_full_scoring_sidecar_summary.md` | Build summary and counts. |
| `observed_row_full_scoring_sidecar_artifact.csv` | Compact review-only observed-row scoring component sidecar. |
| `observed_row_full_scoring_sidecar_schema.csv` | Sidecar schema. |
| `observed_row_full_scoring_coverage_matrix.csv` | Component coverage and blocker matrix. |
| `blocked_components_report.md` | Blocked direct/subtype components and omitted direct zero expansion. |
| `zero_row_policy_report.md` | Explicit zero and missing-row policy. |
| `scoring_formula_guardrail_report.md` | Formula and approval guardrails. |
| `parity_rerun_handoff.md` | Handoff to label parity rerun. |
| `merge_safety_report.md` | Merge safety report. |
