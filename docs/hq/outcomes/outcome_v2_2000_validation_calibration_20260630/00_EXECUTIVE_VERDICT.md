# Outcome V2 2000-2024 Validation/Calibration Gate - Executive Verdict

## Verdict

`YELLOW_PARTIAL_REVIEW_ONLY_APPROVAL`

The 2000-2024 exact-scoring historical label extension improves Outcome V2
historical validation coverage enough to approve one previously blocked field
for historical review-only use:

- `RB_T12_WITHIN_5Y`: `APPROVE_REVIEW_ONLY`

One previously blocked field remains blocked:

- `RB_T6_WITHIN_5Y`: `KEEP_BLOCKED_WEAK_CALIBRATION`

This is not a current-player activation. It does not approve app-facing
probabilities, Rankings integration, model inputs, source-truth promotion, or
protected artifact updates.

## Branch / Base

- Branch: `work/outcome-v2-2000-validation-calibration-20260630`
- Worktree: `C:\NWR\Niners-War-Room-outcome-v2-2000-validation-calibration-20260630`
- Base: `origin/work/hq-parallel-control`
- Base HEAD: `899e2276fc69041ef36d037cfb50c4b85e679232`

## Inputs

2000-2024 exact-scoring dry-run labels:

- `C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_2000_probe\outcome_v2_extended_season_outcome_labels.csv`
- `C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_2000_probe\outcome_v2_extended_anchor_horizon_labels.csv`

Prior 2000 coverage probe packet:

- `C:\NWR\Niners-War-Room-outcome-v2-2000-coverage-probe-20260630\docs\hq\outcomes\outcome_v2_2000_coverage_probe_20260630\`

2000-2024 validation outputs generated outside git:

- `C:\NWR_SHARED_DATA\outcome_v2_horizon\validation_2000_probe\outcome_v2_probability_validation_results.csv`
- `C:\NWR_SHARED_DATA\outcome_v2_horizon\validation_2000_probe\outcome_v2_probability_calibration_buckets.csv`
- `C:\NWR_SHARED_DATA\outcome_v2_horizon\validation_2000_probe\outcome_v2_probability_model_bucket_rates.csv`
- `C:\NWR_SHARED_DATA\outcome_v2_horizon\validation_2000_probe\outcome_v2_probability_validation_manifest.csv`

## Coverage Summary

| Metric | 2012-2024 baseline | 2000-2024 validation gate |
| --- | ---: | ---: |
| Season label rows | 7,440 | 13,652 |
| Anchor horizon rows | 7,440 | 13,652 |
| Complete this-year rows | 5,066 | 9,731 |
| Complete next-year rows | 3,771 | 7,566 |
| Complete within-5Y rows | 1,064 | 2,701 |
| Scoring mode | `exact_verified_first_downs` | `exact_verified_first_downs` |

## Field Decisions

| Decision | Count |
| --- | ---: |
| `APPROVE_REVIEW_ONLY` | 35 |
| `KEEP_BLOCKED_WEAK_CALIBRATION` | 1 |
| `KEEP_BLOCKED_INSUFFICIENT_SAMPLE` | 0 |
| `KEEP_BLOCKED_IDENTITY_OR_FEATURE_GATE` | 0 |
| `NEEDS_MORE_INFO` | 0 |

## RB Elite 5Y Decisions

| Field | Decision | Why |
| --- | --- | --- |
| `RB_T6_WITHIN_5Y` | `KEEP_BLOCKED_WEAK_CALIBRATION` | Larger sample improves Brier delta, but max large-bucket calibration error is `0.331193`, above the `0.30` guard. |
| `RB_T12_WITHIN_5Y` | `APPROVE_REVIEW_ONLY` | Complete rows increase from `224` to `586`; held-out Brier beats prevalence and calibration passes. |

## Era Effect Note

Era effects are visible, especially for RB 5Y fields. The 2018-2019 holdout
RB T6 within-5Y hit rate is `0.426230`, versus `0.238579` for 2000-2005,
`0.284848` for 2006-2011, and `0.208589` for 2012-2017. That shift is material
and supports keeping `RB_T6_WITHIN_5Y` blocked.

`RB_T12_WITHIN_5Y` also shows era variation, but the 2000-2024 validation run
passes both the Brier and calibration guards. Approval is limited to historical
review-only use.

## Non-Activation Statement

This gate does not:

- Create current-player probabilities.
- Wire probabilities into Rankings.
- Change Dynasty Rank, final board rank, tiers, hidden sort keys, model scores,
  source-truth gates, or protected artifacts.
- Promote CFBD, NFL usage, DynastyProcess, Gmail, vendor, proxy, market, ADP,
  or analyst data into model inputs.
- Treat missing/censored labels as misses, zeros, healthy, clean, low-risk, or
  false.

Missing data remains `Not enough information`.
