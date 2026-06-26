# NFL Usage Final Integration Candidate Report V0

Overall verdict: GREEN integration candidate for review-only merge; no active model input.

Merge-ready status: yes, after reconciliation with parallel CFBD branch.

Base branch: `origin/work/hq-parallel-control`.
Branch: `work/nfl-usage-target-backtest-v0`.

Historical expansion result: feature seasons 2018;2019;2020;2021;2022;2023 attempted; joined leakage-safe rows 2848.
Feature seasons used: 2018;2019;2020;2021;2022;2023.
Target seasons used: 2019;2020;2021;2022;2023;2024.

Backtest result summary:
- `touches` vs `next_season_nwr_points`: 0.607561
- `opportunities` vs `next_season_nwr_points`: 0.603754
- `touches` vs `next_season_nwr_points_per_game`: 0.58646
- `red_zone_touches` vs `next_season_nwr_points`: 0.57233
- `opportunities` vs `next_season_nwr_points_per_game`: 0.567087
- `red_zone_touches` vs `next_season_nwr_points_per_game`: 0.557115
- `offense_snaps` vs `next_season_nwr_points`: 0.546662
- `inside_10_touches` vs `next_season_nwr_points`: 0.533531

Fields approved for display-only context:
- `offense_snaps`
- `offense_pct`
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

Fields upgraded to model-candidate pending manual review:
- `targets`
- `carries`
- `receptions`
- `touches`
- `opportunities`
- `rushing_yards`
- `receiving_yards`
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

Fields still research-only:
- `ngs_efficiency_fields`
- `participation_personnel_formation_context`
- `route_participation_proxy`
- `tprr_like_proxy`
- `yprr_like_proxy`
- `ftn_pfr_advanced_fields`

Licensed-data gaps:
- `true_routes_run`
- `true_tprr`
- `true_yprr`

Remaining blockers: manual review and an explicit later promotion gate are required before any usage field can become model input.

No-CFBD confirmation: CFBD was not read, written, or used.
No-app-decision-wiring confirmation: no app page, navigation, or decision behavior was changed.
No-model-input confirmation: all artifacts keep `model_input_allowed=no`.
Raw-data tracking confirmation: raw and row-level expanded panels are under ignored shared cache only.

Merge/reconciliation notes: merge this NFL usage branch only after CFBD branch reconciliation, then run post-merge smoke checks for target/backtest CSVs, app routes, frozen board row count, and pinned hash.
