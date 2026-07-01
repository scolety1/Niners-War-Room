# NWR Historical Tuning Substrate Expansion V3 Source Semantics Audit

Verdict: `GREEN_SOURCE_SEMANTICS_AUDIT_WITH_CLEANER_V3_SUBSTRATE_REVIEW_ONLY_NOT_TUNING_READY`

V3 is a source-semantics and substrate-cleanliness lane. It did not run formula search, optimize formulas, train a production model, change rankings, wire app behavior, or promote any source truth.

## Result

- Branch: `work/historical-tuning-substrate-expansion-v3-source-semantics-audit-20260701`
- Base HEAD: `5684ea7b2e6e61f8d68308a6705c2421622f3f98`
- Full substrate artifact: `nwr_historical_tuning_feature_target_substrate_v3.parquet`
- Full substrate SHA-256: `6b80a71af609932c91553413319902d2a61a4b24c36060d3c724747672f9797a`
- Rows: `5,518` (`+0` vs V2)
- Feature seasons: `2012-2024`
- Target seasons: `2013-2025`
- Position rows: `{'QB': 754, 'RB': 1429, 'TE': 1211, 'WR': 2124}`
- Feature decisions emitted: `22` allowed review-only features, `4` null-fenced features, `5` blocked or absent feature families

## Decision

V3 produces a cleaner review-only substrate and reusable source-semantics matrices. Core Backtest V1 zeros are now classified column by column. Optional snap and air-yard/YAC source-missing zeros remain replaced with nulls. Future formula tuning is still not production-viable until a separate human review accepts the V3 allowlist and decides whether to regenerate a production-grade source table.
