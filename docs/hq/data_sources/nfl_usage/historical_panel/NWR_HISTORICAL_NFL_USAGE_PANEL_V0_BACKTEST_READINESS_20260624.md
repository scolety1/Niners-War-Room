# Historical NFL Usage Panel V0 Backtest Readiness

## Is Predictive Backtest Still Blocked?

Yes, but the blocker has narrowed. Historical coverage artifacts and local/shared-cache panels now exist for core usage fields, but predictive backtesting should remain blocked until a separate backtest lane connects these panels to approved target labels, validates leakage windows end to end, and runs ablations.

## Exact Remaining Blockers

- Target labels remain conditionally approved from prior local Backtest V0 work and need a committed target manifest for this usage-panel lane.
- Snap share fields have identity/join caveats because snap counts use PFR/player-name context rather than direct GSIS IDs.
- Red-zone and inside-10/inside-5 fields are coverage-ready with small-sample caveats.
- Research-only and licensed-gap fields remain out of predictive scope.

## Fields With Enough Historical Coverage

- `targets`
- `carries`
- `receptions`
- `touches`
- `opportunities`
- `rushing_yards`
- `receiving_yards`
- `receiving_air_yards`
- `receiving_yards_after_catch`
- `rushing_first_downs`
- `receiving_first_downs`
- `red_zone_carries`
- `red_zone_targets`
- `red_zone_touches`
- `inside_10_carries`
- `inside_10_targets`
- `inside_10_touches`
- `inside_5_carries`
- `inside_5_targets`
- `inside_5_touches`

## Fields With Coverage Caveats

- `offense_snaps`
- `offense_pct`

## Fields Remaining Display-Only Only

All coverage-ready fields remain display/review-only until a future promotion/backtest lane approves more. No model input is enabled here.

## Fields Remaining Research-Only

- `ngs_efficiency_fields`
- `participation_personnel_formation_context`
- `route_participation_proxy`
- `tprr_like_proxy`
- `yprr_like_proxy`
- `ftn_pfr_advanced_fields`

## Licensed-Data Gaps

- `true_routes_run`
- `true_tprr`
- `true_yprr`

## Target Labels Still Needed

Use only approved future outcome labels such as `next_nwr_points`, `next_nwr_ppg`, and position finish flags from a committed target manifest. Do not use ADP, market, DynastyProcess, ranks, projections, or vendor values.

## Generated Local Panels

- `player_week_core_usage_panel (18296 rows)`
- `player_season_core_usage_panel (1840 rows)`
- `player_week_redzone_usage_panel (7830 rows)`
- `player_season_redzone_usage_panel (1435 rows)`
- `player_season_usage_rolling_features_panel (18296 rows)`

## Safest Next Step

Run a separate historical usage backtest lane that reads the shared-cache panels, joins approved target labels by player/season, validates season-N to season-N+1 leakage rules, and reports field-family ablations without enabling model input.
