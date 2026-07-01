# Merge Safety Report

Verdict: `GREEN_REVIEW_ONLY_ARTIFACT_BRANCH`

Allowed changed paths:

- `docs/hq/experiments/historical_formula_tuning_sandbox_v1_20260701/`
- `tests/test_historical_formula_tuning_sandbox_v1_20260701.py`

Protected paths intentionally unchanged:

- `app/`
- `src/`
- production model/ranking/service code
- production formula/config files
- source-truth or latest-approved data paths

Raw/shared/cache/local files are not tracked. Local generated Backtest V1 paths are referenced only as source evidence and summarized into derived CSV/Markdown artifacts.

## Validation

Changed-path scan found only:

- `docs/hq/experiments/historical_formula_tuning_sandbox_v1_20260701/`
- `tests/test_historical_formula_tuning_sandbox_v1_20260701.py`

No app/model/rank/source-truth/runtime paths are changed.
