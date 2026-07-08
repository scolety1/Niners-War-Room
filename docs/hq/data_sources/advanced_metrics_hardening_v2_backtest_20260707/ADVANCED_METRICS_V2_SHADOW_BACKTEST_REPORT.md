# Advanced Metrics V2 Shadow Backtest Report

V2 ran only for feature groups that passed the hardening gate: baseline, baseline plus NGS, and baseline plus NGS plus ffopportunity stress-test fields. PFR, ESPN, FTN, routes, TPRR, YPRR, `rz_att`, and elusive proxy were excluded.

## Aggregate Results

- QB baseline: MAE 3.852759, lift 0.0, mixed_or_noisy
- QB baseline_plus_NGS: MAE 3.957925, lift -0.105167, decline_or_noisy
- QB baseline_plus_NGS_ffopportunity: MAE 4.124898, lift -0.272139, decline_or_noisy
- RB baseline: MAE 2.455837, lift 0.0, mixed_or_noisy
- RB baseline_plus_NGS: MAE 2.484177, lift -0.02834, mixed_or_noisy
- RB baseline_plus_NGS_ffopportunity: MAE 2.43291, lift 0.022927, mixed_or_noisy
- WR baseline: MAE 1.801033, lift 0.0, mixed_or_noisy
- WR baseline_plus_NGS: MAE 1.77083, lift 0.030203, mixed_or_noisy
- WR baseline_plus_NGS_ffopportunity: MAE 1.751289, lift 0.049744, mixed_or_noisy
- TE baseline: MAE 1.252826, lift 0.0, mixed_or_noisy
- TE baseline_plus_NGS: MAE 1.226867, lift 0.025959, mixed_or_noisy
- TE baseline_plus_NGS_ffopportunity: MAE 1.21332, lift 0.039506, mixed_or_noisy

Interpretation: positive lift means lower MAE than baseline. Results are mixed and not production-ready.
