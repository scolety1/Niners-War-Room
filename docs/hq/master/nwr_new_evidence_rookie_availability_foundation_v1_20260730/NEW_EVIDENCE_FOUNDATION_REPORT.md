# NWR New Evidence Foundation V1

## Result

`YELLOW_NWR_NFLVERSE_ADMITTED_CFBD_BLOCKED`

Partial source-admission status: `NFLVERSE_ADMITTED_CFBD_NOT_ADMITTED`.

Admitted nflverse datasets: combine, depth_charts, draft_picks, injuries, participation, player_stats_seasonal, player_stats_weekly, players, seasonal_rosters, snap_counts, weekly_rosters. Source snapshots cover 2012-2025
for the core NFL panels, with identity/draft/combine master files and explicit
coverage limits. Rookie foundation: 2,862 rows across
2012-2026. Early-career foundation: 6,577 rows across
2012-2025. Availability foundation: 12,243 rows across
2012-2025.

## Identity and Temporal Safety

Exact mappings: 43,133; review-only: 0; unresolved: 3,789.
Every training/evaluation fold is chronological; season-end opportunity never
predicts an earlier same-season event. Missing injury records are never interpreted
as healthy, undrafted players remain present, and missing combine values remain
missing with indicators.

## Incremental Value

Useful source families: draft_capital, early_nfl_opportunity, age_position, injury_practice, snaps_participation_depth. Source families admitted but not
incremental in this run: draft_age, combine. CFBD R4 is not evaluated because
the owner-controlled credential is absent. These results authorize data
foundations only; they do not authorize a rookie ranking or formula search.
