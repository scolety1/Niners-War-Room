# Feature Generation Path Report

## Path Used

Existing script: `scripts/build_backtest_dataset_v1.py`

The script was run with the approved `nflreadpy` pydeps path and produced local-only artifacts under:

`C:\NWR_SHARED_DATA\backtests\historical_tuning_substrate_expansion_v2_20260701_2012_2025`

## Coverage

- Feature seasons: `2012-2024`
- Target seasons: `2013-2025`
- Rows: `5,518`
- Delta vs V1: `+2,410`

## Exclusions

The V2 canonical parquet excludes current-only roster/status/injury/depth/schedule context, route fields, route proxies, TPRR, YPRR, ambiguous `rz_att`, market/ADP/vendor/projection/rank fields, and red-zone fields pending a separate typed historical sidecar gate.
