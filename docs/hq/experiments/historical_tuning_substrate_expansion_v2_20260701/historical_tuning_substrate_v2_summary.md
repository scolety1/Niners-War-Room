# NWR Historical Tuning Substrate Expansion V2

Verdict: `GREEN_RUNTIME_RESTORED_YELLOW_SUBSTRATE_EXPANDED_REVIEW_ONLY_NOT_TUNING_READY`

V2 restored the approved local nflreadpy runtime path for artifact generation and expanded the review-only feature-target substrate. It did not run formula search, optimize formulas, change production formulas, update rankings, or wire any runtime behavior.

## Result

- Branch: `work/historical-tuning-substrate-expansion-v2-20260701`
- Base HEAD: `31c596418ea0217c80f01f955ab6230113936540`
- Full substrate artifact: `nwr_historical_tuning_feature_target_substrate_v2.parquet`
- Full substrate SHA-256: `58ac7e03d1a276ddae6a375fbc5e75778f10b6e94cf315bc67751deb322cc1d5`
- Rows: `5,518` (`+2,410` vs V1)
- Feature seasons: `2012-2024`
- Target seasons: `2013-2025`
- Position rows: `{'QB': 754, 'RB': 1429, 'TE': 1211, 'WR': 2124}`
- Optional source null-fenced rows: `1,371`

## Decision

The runtime blocker is fixed for review-only artifact generation by using the repo-approved shared pydeps path. The substrate is wider and cleaner than V1, but legacy source semantics remain partially fenced rather than fully eliminated. Future formula tuning is still not production-viable without human review and a V3 source-semantics pass.
