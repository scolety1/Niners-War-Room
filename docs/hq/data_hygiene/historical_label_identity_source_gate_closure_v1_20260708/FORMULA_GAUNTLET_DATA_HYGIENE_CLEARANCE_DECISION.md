# Formula Gauntlet Data Hygiene Clearance Decision

## Verdict

`YELLOW_DATA_HYGIENE_CLEARS_COMPONENT_SIGNAL_TESTS_ONLY`

## Maximum Cleared Level

`CLEARED_FOR_REVIEW_ONLY_COMPONENT_SIGNAL_TESTS`

## Cleared

Data Hygiene clears these activities, pending separate Master HQ execution approval:

- Review-only component signal tests on the existing partial historical panel.
- PYF anchor comparisons.
- Position-level reporting for component signals.
- Sparse-history and prior-production-decline diagnostics as reports.
- Source/use-gate status reporting.

## Not Cleared

Data Hygiene does not clear:

- `CLEARED_FOR_REVIEW_ONLY_POSITION_SCOPED_TOURNAMENTS`
- `CLEARED_FOR_FULL_REVIEW_ONLY_FORMULA_GAUNTLET`
- Exact Model v4 replay.
- Formula candidate generation.
- Formula tuning or optimization.
- Formula winners.
- Production rankings.
- Source promotion.
- App/runtime behavior.

## Why

The label, identity, missingness, and leakage evidence is strong enough for component signal tests using the existing partial replay substrate. It is not strong enough for tournaments because source gates remain review-only, exact Model v4 historical receipts are missing, route/YPRR/TPRR are blocked, and missingness/sparse-history thresholds are not yet formalized as tournament stop conditions.

## Master HQ Boundary

This decision is a Data Hygiene recommendation only. Master HQ owns execution approval, promotion decisions, Formula Gauntlet scope, and any later merge/push decision.
