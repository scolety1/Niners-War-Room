# Human Review Update

The rescue sprint gives Tim a useful update, not an approval path.

Review order:

1. Compare `qb_guard_soft_blend` with the original candidate in `validation_metric_comparison.csv` and `holdout_metric_comparison.csv`.
2. Review `elite_qb_regression_comparison.csv`; the soft QB guard is the cleanest elite-QB risk reducer.
3. Review `cutline_regression_comparison.csv`; the cutline issue is still unresolved for the best partial rescue.
4. Review `topn_startable_rescue_report.csv`; conservative variants can trade off bucket/startable behavior.

Recommended human decision: keep `usage_opportunity_volume` on HOLD. A future branch could separately inspect cutline-safe guards, but that should be explicit and still review-only.
