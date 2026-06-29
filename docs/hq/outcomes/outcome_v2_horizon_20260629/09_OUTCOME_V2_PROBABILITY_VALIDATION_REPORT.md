# Outcome V2 Probability Validation Report - 2026-06-30

## Verdict

`GREEN_PARTIAL_FIELDS_VALIDATED`

Historical validation passed for 22 this-year / next-year fields. Fourteen fields remain blocked.

No current-player artifact or Rankings integration is approved by this report alone.

## Validation Method

The validation service uses a conservative, no-new-dependency empirical model:

- Join each anchor row to same-anchor-season factual outcome features.
- Use only approved factual historical context from the Outcome V2 label factory artifacts.
- Bucket players by prior anchor-season position finish relative to the same threshold:
  - `prior_threshold_hit`
  - `near_threshold`
  - `depth_relevant`
  - `active_low_finish`
  - `limited_or_inactive`
  - `missing_or_no_prior_production`
- Estimate shrunk empirical train rates by bucket.
- Compare held-out Brier score against a smoothed prevalence baseline.

Held-out seasons:

- This-year fields: validate on anchor seasons 2022 and 2023.
- Next-year fields: validate on anchor seasons 2021 and 2022.

No market, ADP, DynastyProcess, CFBD, projections, vendor rankings, medical projections, Dynasty Rank, or NWR Dynasty Score inputs are used.

## Generated Shared-Data Artifacts

Generated under:

`C:\NWR_SHARED_DATA\outcome_v2_horizon\validation\`

Files:

- `outcome_v2_probability_validation_results.csv`
- `outcome_v2_probability_calibration_buckets.csv`
- `outcome_v2_probability_model_bucket_rates.csv`
- `outcome_v2_probability_validation_manifest.csv`

These are generated review artifacts and are not tracked in git.

## Passed Fields

22 fields passed held-out Brier comparison against prevalence:

| Field | Validation Rows | Positives | Model Brier | Baseline Brier |
|---|---:|---:|---:|---:|
| QB T6 This Year | 126 | 11 | 0.065576 | 0.080011 |
| QB T12 This Year | 126 | 21 | 0.114832 | 0.139890 |
| QB T6 Next Year | 110 | 11 | 0.081762 | 0.090073 |
| QB T12 Next Year | 110 | 20 | 0.123722 | 0.148762 |
| RB T6 This Year | 223 | 12 | 0.045351 | 0.050932 |
| RB T12 This Year | 223 | 21 | 0.076089 | 0.085331 |
| RB T24 This Year | 223 | 44 | 0.115196 | 0.158862 |
| RB T36 This Year | 223 | 67 | 0.144046 | 0.211206 |
| RB T24 Next Year | 181 | 30 | 0.118666 | 0.138683 |
| RB T36 Next Year | 181 | 49 | 0.163318 | 0.197472 |
| WR T6 This Year | 337 | 10 | 0.025409 | 0.028802 |
| WR T12 This Year | 337 | 20 | 0.048655 | 0.055881 |
| WR T24 This Year | 337 | 41 | 0.073886 | 0.106873 |
| WR T36 This Year | 337 | 61 | 0.091769 | 0.148248 |
| WR T6 Next Year | 276 | 10 | 0.032491 | 0.034921 |
| WR T12 Next Year | 276 | 20 | 0.054565 | 0.067269 |
| WR T24 Next Year | 276 | 36 | 0.082800 | 0.113517 |
| WR T36 Next Year | 276 | 52 | 0.107438 | 0.152964 |
| TE T6 This Year | 193 | 10 | 0.035363 | 0.049240 |
| TE T12 This Year | 193 | 22 | 0.083579 | 0.101061 |
| TE T6 Next Year | 158 | 9 | 0.048699 | 0.053902 |
| TE T12 Next Year | 158 | 18 | 0.079483 | 0.101301 |

## Validation-Weak Fields

Two fields had enough labels, but failed held-out Brier comparison:

- RB T6 Next Year
- RB T12 Next Year

These must stay blocked.

## Five-Year Fields

All within-next-5-years fields remain blocked.

Reason:

- only 296 complete rows total
- only 2018 and 2019 are complete anchor seasons
- 3,273 rows are right-censored or missing

Do not expose 5Y probabilities in Rankings from the current label factory.

## Calibration Summary

Calibration buckets were generated for every validated field. Because this is a simple empirical bucket model, calibration should be treated as review-only and conservative. It is good enough to continue to a current-player feature coverage gate, not enough by itself to approve app display.

## Missing Data Policy

Rows without complete labels or features remain `Not enough information`.

Missing/censored data is not converted to zero, false, a miss, clean health, or low risk.

## Next Gate

Proceed to current-player feature coverage only for the 22 passed fields.
