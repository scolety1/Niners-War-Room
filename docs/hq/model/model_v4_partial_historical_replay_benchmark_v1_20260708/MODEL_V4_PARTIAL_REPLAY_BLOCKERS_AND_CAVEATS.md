# Model v4 Partial Replay Blockers And Caveats

## Hard Caveats

- This is not exact Model v4 replay.
- This is not production model accuracy.
- No predeclared partial Model v4 score exists, so no score was invented.
- No source was promoted.
- No formula weights were tuned or optimized.
- Production-active status remains blocked.
- Historical accuracy remains unproven for exact Model v4.

## Exact Replay Blockers

1. Missing season-by-season `checkpoint_review_score` receipts.
2. Missing season-by-season `position_specific_review_score` receipts.
3. Missing lifecycle, age, role, and confidence receipts.
4. Missing WR/QB v2 candidate-overlay receipt chain.
5. Missing exact route/YPRR/TPRR/red-zone normalized component receipts.
6. `shadow_model_v2_metrics.csv` remains unavailable for exact shadow/guardrail replay if required.

## Leakage Guardrail

- Leakage guardrail errors: `0`
- All panel rows use `feature_season = target_season - 1` and pass the existing leakage/as-of flags.
