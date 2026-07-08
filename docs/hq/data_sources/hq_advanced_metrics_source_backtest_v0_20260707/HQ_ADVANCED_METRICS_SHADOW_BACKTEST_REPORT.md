# HQ Advanced Metrics Shadow Backtest Report

Backtest status: review-only, mixed/partial.

Policy: season-forward validation using feature season N and target season N+1 from the canonical V3 substrate. The shadow test compares simple baseline canonical usage features against advanced-metric augmented feature sets where ID-safe joins were available.

## Aggregate Results

- QB baseline_core_usage: MAE 3.817068, baseline MAE delta 0, test rows 184
- QB baseline_plus_position_ngs: MAE 4.313763, baseline MAE delta -0.496694, test rows 107
- QB baseline_plus_position_ngs_ffopp: MAE 4.412177, baseline MAE delta -0.595109, test rows 107
- RB baseline_core_usage: MAE 2.495196, baseline MAE delta 0, test rows 307
- RB baseline_plus_position_ngs: MAE 3.318352, baseline MAE delta -0.823156, test rows 144
- RB baseline_plus_position_ngs_ffopp: MAE 3.357235, baseline MAE delta -0.86204, test rows 144
- WR baseline_core_usage: MAE 1.808989, baseline MAE delta 0, test rows 488
- WR baseline_plus_position_ngs: MAE 2.04751, baseline MAE delta -0.238521, test rows 238
- WR baseline_plus_position_ngs_ffopp: MAE 2.073243, baseline MAE delta -0.264254, test rows 238
- TE baseline_core_usage: MAE 1.269951, baseline MAE delta 0, test rows 291
- TE baseline_plus_position_ngs: MAE 1.441035, baseline MAE delta -0.171084, test rows 110
- TE baseline_plus_position_ngs_ffopp: MAE 1.625041, baseline MAE delta -0.35509, test rows 110

Positive baseline delta means lower MAE than baseline. Results are not production evidence and should not be treated as formula approval. Coverage and 2025 caveats remain material.
