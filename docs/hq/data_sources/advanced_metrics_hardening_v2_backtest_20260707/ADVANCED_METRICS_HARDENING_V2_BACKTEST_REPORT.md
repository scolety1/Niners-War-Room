# Advanced Metrics Hardening V2 Backtest Report

Verdict: `YELLOW_ADVANCED_METRICS_V2_BACKTEST_MIXED`

Branch: `work/lane-advanced-metrics-hardening-v2-backtest-20260707`
HEAD at generation: `602b95752384fd7e311c6858985fa81f36e0029d`
V0 packet tracked: `yes`

This packet hardens the committed V0 evidence rather than rerunning V0 exactly. NGS remains the only broadly ID-safe family. PFR and ESPN are blocked for V2 modeling tests by identity bridge gaps. FTN is blocked by semantics/aggregation uncertainty. ffopportunity is partial and included only in review-only V2 stress tests with missingness indicators.

## V2 Backtest Summary

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

No result is production evidence. No rankings formula, app UI, hidden sort, recommendation, or source-truth behavior changed.
