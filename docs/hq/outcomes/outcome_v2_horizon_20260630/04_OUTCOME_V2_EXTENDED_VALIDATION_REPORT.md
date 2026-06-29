# Outcome V2 Extended Validation Report

Date: 2026-06-29

## Verdict

`GREEN_EXTENDED_VALIDATION_COMPLETE`

Outcome V2 extended validation was rerun against the 2012-2024 historical label extension. The validation gate is now field-specific and includes both held-out Brier performance versus baseline and a calibration-quality guard.

No field is activated only because coverage improved. Fields still have to pass validation.

## Inputs

Extended season labels:

`C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_labels_extended\outcome_v2_extended_season_outcome_labels.csv`

Extended anchor horizon labels:

`C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_labels_extended\outcome_v2_extended_anchor_horizon_labels.csv`

Validation output root:

`C:\NWR_SHARED_DATA\outcome_v2_horizon\validation_extended\`

## Historical Coverage

| Metric | Value |
| --- | ---: |
| Season labels | 7,440 |
| Anchor horizon labels | 7,440 |
| Seasons covered | 2012-2024 |
| Scoring mode | `exact_verified_first_downs` |
| Complete 5Y rows | 1,064 |
| QB complete 5Y rows | 203 |
| RB complete 5Y rows | 224 |
| WR complete 5Y rows | 395 |
| TE complete 5Y rows | 242 |

## Validation Method

Each candidate field is tested only on complete, uncensored labels. Missing or censored windows are not treated as misses.

Validation requires:

- at least 100 complete label rows
- at least 20 positive labels
- at least five complete anchor seasons
- held-out empirical model Brier score less than or equal to baseline prevalence Brier
- acceptable calibration review

Calibration review blocks a field when weighted absolute calibration error exceeds `0.15` or a large bucket has absolute calibration error above `0.30`.

## Summary

| Horizon | Passed | Blocked |
| --- | ---: | ---: |
| This Year | 12 | 0 |
| Next Year | 12 | 0 |
| Within 5 Years | 10 | 2 |
| Total | 34 | 2 |

## Validated Fields

- `QB_T6_THIS_YEAR`
- `QB_T12_THIS_YEAR`
- `QB_T6_NEXT_YEAR`
- `QB_T12_NEXT_YEAR`
- `QB_T6_WITHIN_5Y`
- `QB_T12_WITHIN_5Y`
- `RB_T6_THIS_YEAR`
- `RB_T12_THIS_YEAR`
- `RB_T24_THIS_YEAR`
- `RB_T36_THIS_YEAR`
- `RB_T6_NEXT_YEAR`
- `RB_T12_NEXT_YEAR`
- `RB_T24_NEXT_YEAR`
- `RB_T36_NEXT_YEAR`
- `RB_T24_WITHIN_5Y`
- `RB_T36_WITHIN_5Y`
- `WR_T6_THIS_YEAR`
- `WR_T12_THIS_YEAR`
- `WR_T24_THIS_YEAR`
- `WR_T36_THIS_YEAR`
- `WR_T6_NEXT_YEAR`
- `WR_T12_NEXT_YEAR`
- `WR_T24_NEXT_YEAR`
- `WR_T36_NEXT_YEAR`
- `WR_T6_WITHIN_5Y`
- `WR_T12_WITHIN_5Y`
- `WR_T24_WITHIN_5Y`
- `WR_T36_WITHIN_5Y`
- `TE_T6_THIS_YEAR`
- `TE_T12_THIS_YEAR`
- `TE_T6_NEXT_YEAR`
- `TE_T12_NEXT_YEAR`
- `TE_T6_WITHIN_5Y`
- `TE_T12_WITHIN_5Y`

## Blocked Fields

| Field | Complete rows | Positives | Validation rows | Model Brier | Baseline Brier | Calibration status | Block reason |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `RB_T6_WITHIN_5Y` | 224 | 60 | 61 | 0.217866 | 0.290400 | `BLOCKED_CALIBRATION_WEAK` | Beats prevalence but weighted calibration error is 0.202095 |
| `RB_T12_WITHIN_5Y` | 224 | 101 | 61 | 0.205358 | 0.278033 | `BLOCKED_CALIBRATION_WEAK` | Beats prevalence but weighted calibration error is 0.185918 and large-bucket error is 0.317420 |

## 5Y Status

5Y fields are no longer globally blocked. The extended labels provide enough complete rows to validate most 5Y fields.

Validated 5Y fields:

- QB T6/T12
- RB T24/T36
- WR T6/T12/T24/T36
- TE T6/T12

Blocked 5Y fields:

- RB T6
- RB T12

Blocked 5Y fields must display `Not enough information` in any future artifact or UI until a later validation gate passes them.

## Guardrails

This validation did not create current-player probabilities, app columns, Rankings wiring, model inputs, rank changes, hidden sort, trade value, pick value, or rookie/prospect outcome probabilities.

Blocked inputs were not used:

- DynastyProcess
- ADP
- market values
- CFBD
- Gmail
- vendor/RotoWire/FantasyPros
- projections
- analyst ranks
- trade values
- true routes / TPRR / YPRR
- injury projections

## Artifacts

- `C:\NWR_SHARED_DATA\outcome_v2_horizon\validation_extended\outcome_v2_probability_validation_results.csv`
- `C:\NWR_SHARED_DATA\outcome_v2_horizon\validation_extended\outcome_v2_probability_calibration_buckets.csv`
- `C:\NWR_SHARED_DATA\outcome_v2_horizon\validation_extended\outcome_v2_probability_model_bucket_rates.csv`
- `C:\NWR_SHARED_DATA\outcome_v2_horizon\validation_extended\outcome_v2_probability_validation_manifest.csv`

These are shared-data review artifacts and are not committed.

## Next Gate

Proceed to the current-player feature/as-of gate. Validation success does not by itself authorize current-player display artifacts or Rankings integration.
