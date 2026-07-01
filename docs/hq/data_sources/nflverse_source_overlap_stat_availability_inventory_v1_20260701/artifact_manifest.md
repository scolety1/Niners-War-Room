# NFLVerse Source Overlap and Stat Availability Inventory V1 Artifact Manifest

Verdict: `YELLOW_STAT_AVAILABILITY_INVENTORY_PARTIAL_SOURCE_GAPS`

## Files

- `source_overlap_inventory_summary.md`
- `master_stat_field_inventory.csv`
- `source_family_coverage_matrix.csv`
- `overlapping_field_matrix.csv`
- `field_accuracy_and_consistency_matrix.csv`
- `missingness_and_leakage_matrix.csv`
- `blocked_or_quarantined_fields.csv`
- `candidate_bucket_summary.csv`
- `recommended_next_lanes.md`
- `guardrail_report.md`
- `merge_safety_report.md`

## Boundary

Inventory only. Every row keeps `model_use_allowed=false`, `training_allowed=false`, and `source_truth_allowed=false`.
