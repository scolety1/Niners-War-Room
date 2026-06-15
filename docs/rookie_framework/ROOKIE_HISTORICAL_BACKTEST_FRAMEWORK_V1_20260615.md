# Rookie Historical Backtest Framework v1

Date: 2026-06-15

Status: scaffold/inventory only. Backtest metrics did not run.

## What Was Built

Created a rookie-only historical backtest framework:

- `scripts/rookie_framework/backtest_rookie_ranking_model_v01.py`
- `tests/test_rookie_backtest_framework_v01.py`

The framework inventories local historical rookie feature data and refuses to compute star-capture or bust-avoidance metrics unless evaluation labels are already present.

## Local Historical Data Found

Historical feature matrix:

`local_exports/model_v4/current_value/latest/full_board_active_support/evidence_matrices/historical_rookie_backtest_feature_matrix.csv`

Inventory result:

- rows: 395
- years: 2021-2025
- positions: QB, RB, TE, WR
- feature columns: 20
- evaluation label columns found: 0

## Why Backtest Metrics Did Not Run

The local file contains historical rookie feature context, but no explicit evaluation labels such as:

- 1-year useful season;
- 2-year value;
- 3-year value;
- starter seasons;
- top-12/top-24/top-36 outcomes;
- league-specific VBD;
- post-rookie fantasy result labels suitable for evaluation.

Outcome labels may be used only as evaluation targets. They were not present, so the framework did not fabricate them.

## Local Outputs

Created under:

`local_exports/rookie_framework/historical_backtest_v1_20260615/`

Outputs:

- `rookie_historical_backtest_inventory_20260615.csv`
- `rookie_historical_backtest_results_v1_20260615.csv`
- `rookie_historical_backtest_metrics_v1_20260615.csv`
- `rookie_historical_backtest_failures_v1_20260615.csv`
- `README_ROOKIE_HISTORICAL_BACKTEST_V1_20260615.md`

The results and metrics files are schema outputs only in this run. The failures file records `missing_evaluation_labels`.

## Leakage Controls

The framework documents these controls:

- no hindsight labels as inputs;
- no post-rookie-season stats as ranking inputs;
- no future injuries or future depth-chart changes as inputs;
- market context, if present, remains audit/display-only;
- outcome labels are evaluation-only when later registered.

## What Remains Missing

Needed before a real backtest can run:

- point-in-time historical feature eligibility policy;
- historical outcome-label file;
- join-key audit between historical features and labels;
- explicit leakage audit for every label;
- year-split or leave-one-year-out validation plan.

## Commands Run

```powershell
python scripts/rookie_framework/backtest_rookie_ranking_model_v01.py
python tests/test_rookie_backtest_framework_v01.py
```

## Production Stop

This framework does not approve production ranking, app wiring, probabilities, bands, private-score changes, outcome columns, or veteran outcome-head usage.

## Rollback Path

Remove the local export directory and revert this framework script/test/doc commit. No production artifact depends on it.
