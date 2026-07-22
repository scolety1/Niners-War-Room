# Historical aging reproducibility

## Authority

This guide reproduces the adopted review-only packet at
docs/hq/master/nwr_post_v1_completeness_historical_aging_audit_v1_20260721.
It does not authorize production tuning.

The leakage-safe panel uses tracked historical evidence, exact identity joins,
and the review-only lifecycle sidecar. Current market ranks, current ADP,
provider calls, future-season values, and current-board ranks are excluded.
The production proxy spans 2013-2025; the comparable out-of-fold panel spans
target seasons 2015-2025.

## Controlling values

- PYF OOF: 4,731 rows, Spearman 0.674674, MAE 21.524413.
- POSITION_BAND_SMALL: 4,728 rows, delta -0.000430.
- MONOTONIC_MILD_CAPPED: 4,728 rows, delta 0.000250.
- MONOTONIC_STRONG_CAPPED: 4,728 rows, delta 0.000894,
  MAE 21.435702, six seasons better and five worse.

Recompute or review the tracked CSVs in this order:

1. BASELINE_HISTORICAL_EVALUATION.csv
2. WALK_FORWARD_VALIDATION_RESULTS.csv
3. OLDER_PLAYER_RESIDUAL_AND_BIAS_ANALYSIS.csv
4. CANDIDATE_ACCEPTANCE_GATE_MATRIX.csv

Every candidate must pass coverage, materiality, repeated-position stability,
position-harm, walk-forward, and severe-false-positive gates. None did.

Result: NO_HISTORICAL_AGE_ADJUSTMENT_CHALLENGER_ADMITTED.

Exact Model v4 replay remains unavailable. Do not claim independent replay,
invent missing outcomes, or change ranks/curves to match the historical packet.
