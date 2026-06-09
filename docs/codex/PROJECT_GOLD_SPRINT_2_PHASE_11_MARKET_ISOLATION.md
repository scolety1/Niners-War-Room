# Project Gold Sprint 2 / Phase 11: Market Isolation

Status: implemented, rankings remain review-only.

## What Changed

- Added explicit market value statuses:
  - `real_imported_market`
  - `stale_market`
  - `missing_market`
  - `disabled_market`
  - `neutral_market_placeholder`
- Added shared market-status helpers in `src/services/market_influence_policy_service.py`.
- Updated stats-first veteran outputs to emit `market_value_status`.
- Blocked neutral/default market values from creating fake `Model vs Market` edges.
- Kept market influence at `0%` for private/model value and keeper value.
- Kept market available only for trade/liquidity/context surfaces.
- Updated War Board, My Team row data, League Targets, Trade Lab rows, and Market Edge reports to use market status.
- Added plain warning translation for neutral, missing, disabled, and stale market values.

## Important Behavior

`market_liquidity = 50` is no longer treated as a real market export unless a row explicitly says the market status is real. When the value is a neutral placeholder, the app keeps the trade market value visible for review context but suppresses usable edge.

Private/model value remains football/stat driven. Extreme market changes do not move:

- `private_lve_value`
- `horizon_retention_score`
- `keeper_score`
- `drop_candidate_score`

Market can still affect:

- `trade_value`
- trade/liquidity rows
- model-vs-market edge when the market input is real
- trade-package/acceptance context

## Tests Added Or Updated

- `tests/test_market_influence_policy_service.py`
- `tests/test_lve_stats_first_veteran_formula_service.py`
- `tests/test_market_edge_service.py`
- `tests/test_command_board_service.py`

Focused verification passed:

- `83 passed`
- Ruff checks passed for touched files.

## Remaining Caveat

This does not make rankings decision-ready. It removes one hidden trust problem: fake market edges from neutral/default market values. Rankings still stay review-only until the broader Project Gold gates pass.
