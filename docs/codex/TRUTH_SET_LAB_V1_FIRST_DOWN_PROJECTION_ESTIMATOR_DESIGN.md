# Truth Set Lab v1 First-Down Projection Estimator Design

## Status

Preview only. This layer does not change active rankings, active projection
scores, active receipts, or decision gates.

## Files

- Projection source: `local_exports/truth_set_lab/v1/source_clean/projections.csv`
- Historical rate source:
  `local_exports/nflverse/preview/sprint2_phase7_public_20260514/raw/nflverse_player_stats_weekly.csv`
- Preview estimates:
  `local_exports/truth_set_lab/v1/reports/first_down_projection_estimator_preview.csv`
- Position rates:
  `local_exports/truth_set_lab/v1/reports/first_down_projection_estimator_rates.csv`
- Summary:
  `local_exports/truth_set_lab/v1/reports/first_down_projection_estimator_summary.csv`

## Design

The current projection recompute layer only counts first-down points when a
projection source gives direct `projected_rushing_first_downs` or
`projected_receiving_first_downs`. The 40-player Truth Set projection file does
not provide those fields, so first-down projection points are intentionally zero
in the active projection recompute.

This preview layer estimates the missing first downs separately:

- `rushing_first_downs = projected_rushing_attempts * historical_first_downs_per_rush`
- `receiving_first_downs = projected_targets * historical_receiving_first_downs_per_target`
- If targets are unavailable but receptions are present:
  `receiving_first_downs = projected_receptions * historical_receiving_first_downs_per_reception`
- `preview_first_down_points = (rushing_first_downs + receiving_first_downs) * 0.4`

Rates are position-specific and are derived from the local nflverse weekly player
stats export.

## Status Labels

- `direct_first_down_projection`: source supplied direct projected rushing or
  receiving first downs.
- `estimated_from_history`: projection volume exists and historical nflverse
  position rates were available.
- `missing_first_down_projection`: no direct first-down projection and no safe
  estimate can be made.

Every row is marked `preview_only_not_active_scoring`.

## Historical Rates From Available nflverse Data

| Position | Rush FD/Rush | Rec FD/Target | Rec FD/Reception |
|---|---:|---:|---:|
| QB | 0.3489 |  | 0.3000 |
| RB | 0.2207 | 0.2571 | 0.3272 |
| WR | 0.3031 | 0.3744 | 0.5916 |
| TE | 0.3929 | 0.3663 | 0.5094 |

These are broad historical position rates, not player-specific or role-specific
rates. They are useful as a design preview, but not enough by themselves to
unlock decision-ready projection scoring.

## Current Truth Set Output

- Projection rows: 40
- Historical nflverse rows reviewed: 10,521
- Positions with historical rates: 4
- Direct first-down projection rows: 0
- Estimated-from-history rows: 37
- Missing first-down projection rows: 3
- Preview first-down points total across the 40-player set: 724.09

## Risks

- Position-level rates hide role differences. A deep-threat WR, power slot, and
  possession WR can have very different first-down conversion profiles.
- RB rates should eventually split carries, targets, red-zone work, and
  short-yardage work. This preview uses broad RB historical rates only.
- QB rushing first downs are meaningful, but passing first downs are not scored
  in LVE and are intentionally ignored.
- The estimates use projected volume from one projection source; if projected
  role is wrong, first-down estimates will be wrong too.
- First-down estimates should be confidence-lowered until validated against
  player-specific historical rates or a paid/source projection feed.

## Recommendation

Keep this estimator as a preview-only audit layer for now. It can help show how
much scoring is missing when projection feeds omit rushing/receiving first
downs, but it should not enter active model scoring until:

1. production and role/usage data are clean,
2. player-specific first-down rates are available where possible,
3. role buckets are separated for RB, WR, and TE,
4. sanity fixtures prove the estimate improves rankings instead of adding noise.
