# NWR Historical Tuning Substrate Expansion V1

Verdict: `YELLOW_SUBSTRATE_VALIDATED_REVIEW_ONLY_NEEDS_SOURCE_EXPANSION_BEFORE_FORMULA_SEARCH`

This lane generated and validated a canonical, review-only season N to season N+1 feature-target substrate. It did not run formula tuning, did not update production formulas, and did not promote any source as production truth.

## Result

- Branch: `work/historical-tuning-substrate-expansion-v1-20260701`
- Base HEAD: `2e11d704179c46bfd72862c660d888de51922271`
- Full substrate artifact: `nwr_historical_tuning_feature_target_substrate_v1.parquet`
- Full substrate SHA-256: `7ca2f05a82fe2804be411e4db1f05bd6f6651c029640c3028f94029e8a185dfe`
- Coverage: 3,108 rows; feature seasons 2018-2024; target seasons 2019-2025; positions QB, RB, TE, WR.
- Position rows: {'QB': 424, 'RB': 789, 'TE': 681, 'WR': 1214}
- Startable target buckets: {'OUTSIDE_STARTABLE': 2589, 'QB_TOP12': 79, 'RB_TOP24': 145, 'TE_TOP12': 76, 'WR_TOP36': 219}

## Interpretation

The available 2018-2024 feature seasons and 2019-2025 target seasons are preserved and validated. Older expansion was attempted through the existing safe Backtest V1 builder, but the approved local nflverse runtime was unavailable, so no older feature rows were admitted.

This is a stronger substrate review packet, not evidence that formula tuning is ready. Future formula work remains YELLOW until older safe feature coverage is expanded and the missingness semantics are reviewed by a human.
