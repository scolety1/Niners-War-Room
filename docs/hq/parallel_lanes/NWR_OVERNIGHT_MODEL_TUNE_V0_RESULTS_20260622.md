# NWR Overnight Model Tune V0 Results - 2026-06-22

Owner: Master/Main HQ

Status: GREEN for completed local-only historical tuning/evaluation. No model
is approved or promoted.

## Scope

This was an evidence-generation run only. It does not approve private value,
rankings, hidden sort, Mock Draft behavior, simulations, final draft advice,
deployment, `latest_candidate`, or `latest_approved`.

Local-only output root:

`C:\NWR_SHARED_DATA\backtests\overnight_model_tune_v0_20260621`

## Run Summary

- Runtime duration: 56.391 seconds
- Position result rows: 64
- Year result rows: 320
- Prediction rows: 36,288
- Positions: QB, RB, WR, TE
- Models: numpy ridge, sklearn ridge, sklearn elastic net, sklearn random forest
- sklearn version: 1.9.0
- Snap-fixed inputs: GREEN

## Guardrails

- Blocked-field scan: PASS
- Leakage scan: PASS
- `SAFE_NO_SNAP`: included as required control
- `SAFE_SNAP_FIXED`: included and usable
- Vendor challenger variants: `VENDOR_YELLOW_HOLD`
- Vendor fields were not joined into safe variants
- No raw vendor rows or prediction tables are included in this repo doc

## Best Variant By Position

| Position | Best variant | Family | Model | Top-N | Spearman | MAE | RMSE |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| QB | `safe_baseline` | `SAFE_BASELINE` | `sklearn_elastic_net` | 0.333 | 0.669 | 59.613 | 78.016 |
| RB | `safe_baseline` | `SAFE_BASELINE` | `sklearn_random_forest` | 0.417 | 0.664 | 43.142 | 58.020 |
| TE | `safe_expanded` | `SAFE_EXPANDED` | `numpy_ridge` | 0.417 | 0.730 | 19.904 | 26.909 |
| WR | `safe_baseline` | `SAFE_BASELINE` | `sklearn_elastic_net` | 0.500 | 0.715 | 30.029 | 39.661 |

## Baseline Comparison

- QB: best result tied the best baseline Top-N; baseline remains preferred.
- RB: best result tied the best baseline Top-N; baseline remains preferred.
- TE: safe expanded/snap-fixed tied best baseline Top-N, but did not pass the
  strict multi-year candidate gate.
- WR: best result was baseline; baseline remains preferred.

## Candidate Summary

- `SAFE_RESEARCH_CANDIDATE`: none
- `VENDOR_RESEARCH_CANDIDATE`: none
- `VENDOR_YELLOW_HOLD`: all planned vendor challenger variants

Baseline winning is acceptable under the approved tuning principles. Current
evidence does not justify promoting a tuned variant.

## Local-Only Reports

- `OVERNIGHT_TUNE_RUN_MANIFEST.csv`
- `OVERNIGHT_TUNE_POSITION_RESULTS.csv`
- `OVERNIGHT_TUNE_YEARLY_RESULTS.csv`
- `OVERNIGHT_TUNE_VARIANT_RANKINGS.csv`
- `OVERNIGHT_TUNE_BLOCKED_FIELD_SCAN.csv`
- `OVERNIGHT_TUNE_LEAKAGE_SCAN.csv`
- `OVERNIGHT_TUNE_WINNERS_BY_POSITION.md`
- `OVERNIGHT_TUNE_FINAL_REPORT.md`

## Verdict

GREEN for completed local-only evaluation and guardrail compliance.

YELLOW for promotion: no variant is approved for model/private-value/ranking or
draft use.
