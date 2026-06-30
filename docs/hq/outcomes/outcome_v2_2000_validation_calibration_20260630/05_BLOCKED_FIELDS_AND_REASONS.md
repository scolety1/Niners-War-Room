# Outcome V2 2000-2024 Validation/Calibration Gate - Blocked Fields And Reasons

## Blocked Field

| Field | Decision | Blocking reason |
| --- | --- | --- |
| `RB_T6_WITHIN_5Y` | `KEEP_BLOCKED_WEAK_CALIBRATION` | Max large-bucket calibration error is `0.331193`, above the `0.30` guard. |

## RB T6 Within 5Y Detail

| Metric | Value |
| --- | ---: |
| Complete rows | 586 |
| Positive rows | 154 |
| Negative rows | 432 |
| Censored/missing rows | 3,023 |
| Validation rows | 61 |
| Validation positives | 26 |
| Brier delta vs prevalence baseline | 0.106046 |
| Weighted calibration absolute error | 0.148866 |
| Max large-bucket calibration absolute error | 0.331193 |

The field beats prevalence on held-out Brier, and the weighted calibration error
is just under the `0.15` guard. The large-bucket calibration error fails the
guard, so the field remains blocked.

## Era Effect Rationale

The era slices support the block:

| Era | Complete rows | Positives | Hit rate |
| --- | ---: | ---: | ---: |
| 2000-2005 | 197 | 47 | 0.238579 |
| 2006-2011 | 165 | 47 | 0.284848 |
| 2012-2017 | 163 | 34 | 0.208589 |
| 2018-2019 holdout | 61 | 26 | 0.426230 |

The held-out 2018-2019 hit rate is materially higher than all training-era
slices. This is not a missing-data issue, but it is a calibration stability
issue. The conservative behavior is to keep `RB_T6_WITHIN_5Y` blocked until a
later lane can validate it with stronger era-aware calibration or additional
approved context.

## Not Blocked After This Gate

`RB_T12_WITHIN_5Y` was previously blocked in the 2012-2024 validation baseline.
The 2000-2024 extension changes its field-level decision to
`APPROVE_REVIEW_ONLY`:

| Metric | Value |
| --- | ---: |
| Complete rows | 586 |
| Positive rows | 280 |
| Validation rows | 61 |
| Brier delta vs prevalence baseline | 0.090988 |
| Weighted calibration absolute error | 0.129218 |
| Max large-bucket calibration absolute error | 0.199917 |

This approval is only for historical review-only use. It does not approve a
current-player display column, current-player probability artifact, Rankings
integration, model input, or protected promotion.

## Missing Data Policy

For all blocked or unactivated contexts:

- Missing data remains `Not enough information`.
- Censored 5Y windows remain `Not enough information`.
- Missing values are not treated as zero, false, clean, healthy, low-risk, or
  misses.

## Future Requirement

A future lane that wants to revisit `RB_T6_WITHIN_5Y` should explicitly test
era-aware calibration and should preserve the same no-leakage, review-only,
non-ranking, non-model-input guardrails.
