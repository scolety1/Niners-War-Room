# Candidate Failure Mode Report

Primary failure modes:

1. Usage proxy drag on elite prior-scoring quarterbacks.
2. Bucket-level Top-N tradeoffs despite better aggregate MAE.
3. Near-cutline player movement that could matter to roster decisions.
4. Possible underweighting of efficient lower-opportunity players.

Stress evidence:

- Severe regression rows in the validation/holdout casebook: `40`
- Elite-QB severe regression rows: `13`
- Material bucket regressions: `4`
- Actual cutline hits moved below a cutline: `8`

Interpretation: these are not leakage or overfit failures, but they are human-review blockers before any shadow-review prep branch.
