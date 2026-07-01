# Missingness Semantics Report

## Verdict

YELLOW: the canonical builder did not convert missing values to zero, but the local Backtest V1 source carries legacy zero-fill semantics for stat absence, unavailable optional sources, and denominator-safe rates.

## Builder Behavior

- No `fillna(0)` or equivalent missing-to-zero conversion is applied by this substrate builder.
- Canonical safe lagged features are selected from the local Backtest V1 source after excluding current-only/depth/status/red-zone fields.
- Derived `prior_touches` and `prior_opportunities` are arithmetic combinations of source V1 component columns.
- Missingness metadata is reported in `feature_coverage_report_v1.csv` and source lineage is retained through `C:\NWR_SHARED_DATA\backtests\backtest_v1_feature_cleanup_20260621\feature_missingness_summary_v1.csv`.

## Source Caveat

The Backtest V1 manifest states:

- role/stat absence can be zero-filled when no usage or unavailable optional source exists
- metadata absence can be zero-filled with explicit missing indicators
- rate denominators can be zero when the denominator is zero or missing

Those source semantics are preserved as review-only context. They are not approved for production modeling or tuning.
