# Sparse-History Refinement Pass/Fail Criteria

- `primary_net_miss_reduction`: >= 12 on at least one full-history or broad-window comparable reference
- `resolved_vs_created`: misses_resolved must meaningfully exceed new_misses_created
- `false_negative`: false-negative reduction must improve without unacceptable false-positive creation
- `severe_false_positive`: no severe false-positive spike
- `spearman_floor`: Spearman must not decline meaningfully; target +0.002 or better
- `top_n`: Top-12/Top-24/Top-36 impact neutral or positive where relevant
- `position_stability`: positive or neutral by position, unless explicitly position-specific
- `collateral`: non-sparse-history collateral damage must stay low
- `partial_window`: partial-window rules stay partial-window only

A refined rule cannot advance if it creates harmful displacement, relies on blocked inputs, blurs partial-window results into full-history claims, or implies production/ranking use.
