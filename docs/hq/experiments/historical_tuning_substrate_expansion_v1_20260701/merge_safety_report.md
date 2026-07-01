# Merge Safety Report

## Expected Changed Paths

All intended changes are limited to:

- `docs/hq/experiments/historical_tuning_substrate_expansion_v1_20260701/`
- `tests/test_historical_tuning_substrate_expansion_v1_20260701.py`

## Protected Paths

No production app/model/rank/source-truth/runtime path is intentionally changed by this lane.

## Artifact Policy

The full parquet is small and review-only, so it is tracked in the experiment artifact directory. Local source CSVs under `C:\NWR_SHARED_DATA` remain untracked.
