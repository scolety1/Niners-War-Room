# Outcome V2 2000-2024 Validation/Calibration Gate - Validation Results

## Validation Runner

Command:

```powershell
python scripts\validate_outcome_v2_probabilities.py --run --output-root C:\NWR_SHARED_DATA\outcome_v2_horizon\validation_2000_probe --anchor-labels-path C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_2000_probe\outcome_v2_extended_anchor_horizon_labels.csv --season-labels-path C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_2000_probe\outcome_v2_extended_season_outcome_labels.csv
```

Output root:

`C:\NWR_SHARED_DATA\outcome_v2_horizon\validation_2000_probe\`

## Result Summary

| Validation status | Fields |
| --- | ---: |
| `PASS_APP_DISPLAY_VALIDATION` | 35 |
| `BLOCKED_CALIBRATION_WEAK` | 1 |

For this gate, `PASS_APP_DISPLAY_VALIDATION` is interpreted only as
`APPROVE_REVIEW_ONLY`. It does not activate current-player display or Rankings
integration.

## Horizon Summary

| Horizon | Passed review-only | Blocked |
| --- | ---: | ---: |
| This year | 12 | 0 |
| Next year | 12 | 0 |
| Within 5Y | 11 | 1 |
| Total | 35 | 1 |

## Previously Blocked RB Elite 5Y Fields

| Field | Complete rows | Positives | Validation rows | Brier delta | Weighted calibration error | Max large-bucket error | Validation status | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `RB_T6_WITHIN_5Y` | 586 | 154 | 61 | 0.106046 | 0.148866 | 0.331193 | `BLOCKED_CALIBRATION_WEAK` | `KEEP_BLOCKED_WEAK_CALIBRATION` |
| `RB_T12_WITHIN_5Y` | 586 | 280 | 61 | 0.090988 | 0.129218 | 0.199917 | `PASS_APP_DISPLAY_VALIDATION` | `APPROVE_REVIEW_ONLY` |

`RB_T6_WITHIN_5Y` nearly clears the weighted calibration guard but fails the
large-bucket calibration guard. It remains blocked and must continue to emit
`Not enough information` anywhere a later artifact would otherwise require it.

`RB_T12_WITHIN_5Y` clears the feasibility, held-out Brier, and calibration
guards in the expanded 2000-2024 historical window. The approval is historical
review-only and does not authorize current-player activation.

## Era Slices For Selected 5Y Fields

| Field | Era | Rows | Positives | Hit rate |
| --- | --- | ---: | ---: | ---: |
| `RB_T6_WITHIN_5Y` | 2000-2005 | 197 | 47 | 0.238579 |
| `RB_T6_WITHIN_5Y` | 2006-2011 | 165 | 47 | 0.284848 |
| `RB_T6_WITHIN_5Y` | 2012-2017 | 163 | 34 | 0.208589 |
| `RB_T6_WITHIN_5Y` | 2018-2019 holdout | 61 | 26 | 0.426230 |
| `RB_T12_WITHIN_5Y` | 2000-2005 | 197 | 87 | 0.441624 |
| `RB_T12_WITHIN_5Y` | 2006-2011 | 165 | 92 | 0.557576 |
| `RB_T12_WITHIN_5Y` | 2012-2017 | 163 | 65 | 0.398773 |
| `RB_T12_WITHIN_5Y` | 2018-2019 holdout | 61 | 36 | 0.590164 |

Era effects are material for RB 5Y fields. This is especially important for
`RB_T6_WITHIN_5Y`, where the holdout hit rate is far above all training-era
slices and the calibration guard fails.

## Missing/Censored Handling

Only complete, uncensored labels were validated. Missing or censored windows
were not treated as misses, zeroes, clean data, healthy outcomes, false labels,
or low risk. They remain `Not enough information`.
