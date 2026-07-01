# Outcome Row-Level Label Source Admission V1 - Artifact Manifest

## Verdict

`GREEN_OUTCOME_ROW_LEVEL_LABEL_SOURCE_ADMITTED_REVIEW_ONLY`

## Base

`origin/work/hq-parallel-control` at `3fca832d3dbefb44cfbceb0f291bfd31f3603fd7`.

## Files

| File | Purpose |
| --- | --- |
| `artifact_manifest.md` | Packet manifest and verdict. |
| `source_admission_summary.md` | Admission decision and source summary. |
| `outcome_label_source_inventory.csv` | Inventory of inspected source candidates. |
| `outcome_row_level_label_source_receipt.csv` | Receipt rows with hashes and approval posture. |
| `outcome_row_level_label_schema_manifest.csv` | Compact source artifact schema. |
| `compact_outcome_row_level_label_source.csv` | Compact tracked review-only row-level Outcome V2 label source. |
| `compact_label_source_coverage_matrix.csv` | Coverage and hit/censoring summary. |
| `censoring_and_missingness_report.md` | Missingness and censoring validation. |
| `label_truth_guardrail_report.md` | No label-truth/model/training/source-truth promotion report. |
| `parity_validator_handoff.md` | Handoff to Label Parity Validator V1 rerun. |
| `merge_safety_report.md` | Protected-surface merge safety report. |

## Compact artifact

- Rows: `119,040`
- SHA256: `7c011459fae2874db3203d99cff4c25405319048a14f7f0e3e73ad1c369d533e`
- Source rows admitted: `7,440` season labels + `7,440` anchor horizon labels
- Source posture: review-only, model/training/app/source-truth closed
