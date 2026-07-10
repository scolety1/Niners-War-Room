# Challenger Gate Decision

## Decision

`RED_REGULARIZED_CHALLENGER_FAILED_TEMPORAL_VALIDATION`

`POSITION_SPECIFIC_RIDGE_ALPHA_1_V1` **fails one or more preregistered historical stability gates and is not eligible for a prospective challenger freeze**.

## Mechanical results

- `headline_improvement`: `PASS`
- `not_isolated`: `PASS`
- `no_repeated_position_regression`: `FAIL`
- `no_severe_fp_increase`: `FAIL`
- `no_favorable_coverage_reduction`: `PASS`
- `uncertainty_review`: `PASS`
- `source_leakage_identity_runtime`: `PASS`

Failed gates: `no_repeated_position_regression|no_severe_fp_increase`.

No aggregate improvement can compensate for a failed repeated-position, severe-FP, coverage, leakage, identity, source, runtime, or uncertainty gate. Exact GAUNTLET_081 remains a locked legacy research reference and is never eligible for the new-challenger label.

`PROSPECTIVE_2026_CHALLENGER_FREEZE.csv` is **intentionally absent because the ridge did not pass every gate**.
