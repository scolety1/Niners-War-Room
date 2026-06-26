# NWR NFL Usage Promotion Review Queue

Date: 2026-06-26

Verdict: GREEN

## Source Files

- `docs/hq/data_sources/nfl_usage/promotion_gate/nfl_usage_field_promotion_decision_matrix_v0.csv`
- `docs/hq/data_sources/nfl_usage/promotion_gate/nfl_usage_backtest_results_v0.csv`
- `docs/hq/data_sources/nfl_usage/promotion_gate/nfl_usage_display_context_sanity_v0.csv`
- `docs/hq/data_sources/nfl_usage/historical_panel/`
- `docs/hq/data_sources/nfl_usage/target_backtest/`

## Counts

Promotion matrix rows: 26

- Approved display-only context: 13
- Display-only candidate: 3
- Research-only: 6
- Licensed-data gaps: 3
- Blocked unsafe: 1
- Approved for model candidate: 0
- Model input allowed: 0
- App wiring allowed: 0

## Morning Queue

Created:

`docs/hq/review_queue/morning_review_20260626/nfl_usage_promotion_review_queue_v1.csv`

Queue rows:

- P0 blocked/licensed/unsafe rows: 4
- P1 display-candidate and proxy-label rows: 6
- P2 display-only/research rows: 16
- Total rows: 26

## Safe Defaults

- `model_input_allowed=no`
- `app_wiring_allowed=no`
- Display-only approved does not mean model-approved.
- Proxies must be labeled as proxies.
- Licensed gaps remain blocked.
- Market/vendor/projection/rank fields remain blocked.

## Human Review Priorities

1. Do not treat true routes, true TPRR, or true YPRR as available public fields.
2. Decide whether red-zone, inside-10, and inside-5 opportunity fields have enough definition/sample-size caveat for display-only use.
3. Keep route participation, TPRR-like, and YPRR-like fields research-only unless explicitly labeled as proxies.
4. Keep all NFL usage fields out of model input until a separate model integration gate.

## Phase 5 Result

Phase 5 is GREEN. The NFL usage queue clarifies display/research/blocked status without enabling model input or app wiring.
