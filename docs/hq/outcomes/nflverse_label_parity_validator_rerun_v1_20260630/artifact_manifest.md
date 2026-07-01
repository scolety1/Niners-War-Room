# NFLVerse Label Parity Validator Rerun V1 - Artifact Manifest

## Verdict

`YELLOW_LABEL_PARITY_RERUN_PARTIAL_SCORING_OR_CENSORING_BLOCKERS`

## Base

`origin/work/hq-parallel-control` at `c5846e6891c8ebd1a4248b8b92f84937941baa3d`.

## Inputs

| Input | Rows | SHA256 |
| --- | ---: | --- |
| NFLVerse player_stats sidecar | 13,628 | `b7f6e237a76b65a75c83543ed64f77525331d87f4e56e3522f4dc52d97a03df8` |
| Outcome row-level label source | 119,040 | `a091048618803b77cec4b263a10a22721771648a46d321fd0f4c02277a952f1c` |

## Files

| File | Purpose |
| --- | --- |
| `artifact_manifest.md` | Packet manifest and verdict. |
| `label_parity_rerun_summary.md` | Executive summary of overlap/parity status. |
| `label_parity_matrix.csv` | Position/family parity decision matrix. |
| `sidecar_label_overlap_matrix.csv` | Position/season overlap accounting. |
| `matched_sidecar_label_rows.csv` | Direct 2024 same-season sidecar-to-season-label overlap rows. |
| `unmatched_sidecar_rows_summary.md` | Summary of unmatched sidecar rows. |
| `unmatched_label_rows_summary.md` | Summary of unmatched label rows. |
| `first_down_parity_report.md` | First-down scoring component parity report. |
| `censoring_parity_report.md` | Censoring and missingness parity report. |
| `label_truth_guardrail_report.md` | No-promotion guardrail report. |
| `next_gate_recommendations.md` | Recommended next gate. |
| `merge_safety_report.md` | Merge safety report. |

## Accounting note

The sidecar contains duplicate source row IDs for some physical rows, so this packet reports sidecar row-record counts for validation accounting. Unique sidecar row IDs are called out separately where relevant.
