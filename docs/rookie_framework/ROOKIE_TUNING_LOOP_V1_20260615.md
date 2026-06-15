# Rookie Tuning Loop v1

Date: 2026-06-15

Status: scaffold only. Tuning did not run.

## What Was Built

Created a guarded rookie-only tuning scaffold:

- `scripts/rookie_framework/tune_rookie_ranking_model_v01.py`
- `tests/test_rookie_tuning_loop_v01.py`

The script checks the historical backtest inventory and refuses to tune unless label-backed backtest data exists.

## Why Tuning Did Not Run

The historical backtest inventory found 395 historical feature rows but no evaluation label columns. Without labels, tuning would overfit or fabricate results, so v1 wrote a not-run recommendation.

## Baseline Retained

The baseline ranking weights remain retained:

- star upside
- early role
- long-term value
- scoring fit
- evidence confidence
- positional adjustment
- bust-risk penalty
- warning penalty

No alternative weights were promoted.

## Local Outputs

Created under:

`local_exports/rookie_framework/tuning_loop_v1_20260615/`

Outputs:

- `rookie_tuning_candidates_v1_20260615.csv`
- `rookie_tuning_results_v1_20260615.csv`
- `rookie_tuning_recommendation_v1_20260615.csv`
- `README_ROOKIE_TUNING_LOOP_V1_20260615.md`

The recommendation is `do_not_tune_yet`.

## Required Gate Before Real Tuning

Before tuning may run:

- point-in-time historical labels must be registered;
- backtest metrics must run;
- validation must use year splits or leave-one-year-out;
- improvements must be compared against the baseline;
- star capture and bust avoidance must both be reported;
- no tuned weights may be promoted without separate approval.

## Commands Run

```powershell
python scripts/rookie_framework/tune_rookie_ranking_model_v01.py
python tests/test_rookie_tuning_loop_v01.py
```

## Production Stop

This scaffold does not approve production ranking integration, app display, private-score replacement, probabilities, bands, outcome columns, hidden sort keys, promoted artifacts, or veteran outcome heads.

## Rollback Path

Remove the local export directory and revert this tuning scaffold script/test/doc commit. No production artifact depends on it.
