# Red-Zone Incremental Value Report

The newly merged typed red-zone sidecar was inventoried but not used for the primary N to N+1 candidate search because admitted 2025 labels are unavailable.

A legacy local-only red-zone rush ablation (`redzone_rush`) was evaluated as context only. It uses `rushes_inside_20`, `rushes_inside_10`, `rushes_inside_5`, and `goal_to_go_rushes`. It does not use ambiguous `rz_att`.

## Result

- validation: MAE improvement `-1.114`, Spearman improvement `-0.004`, Top-N improvement `-0.045`.
- holdout: MAE improvement `-1.230`, Spearman improvement `-0.011`, Top-N improvement `-0.052`.

Verdict: no red-zone incremental value is established for this lane. Future review should wait for typed red-zone sidecar overlap with admitted N to N+1 labels.
