# RotoWire Local Source Contract - 2026-06-08

RotoWire data used here is a user-provided local subscription export/snapshot. The app makes no live RotoWire calls, performs no scraping, and stores no credentials, cookies, tokens, or account/session data.

## Files Used

- `local_exports/model_v4/workouts/latest/rotowire_workout_stats_may25.csv`
- `local_exports/model_v4/depth_charts/latest/rotowire_upcoming_depth_charts_may22.csv`

## Allowed Use

- Current NFL team/status display.
- Identity/team source repair.
- Injury/status context.
- Warning/data-needed explanation.
- Source quarantine resolution.
- Role/depth-chart context only where an existing source-safe pipeline explicitly allows it.

## Blocked Use

- NWR Dynasty Score, NWR Rank, tier, formula weights, VORP/replacement, market/league gaps, public ranking replacement, trade/cut/draft recommendations, or outcome percentages.
- RotoWire projections, rankings, fantasy points, ADP, salaries, DFS values, or market-like fields cannot affect private NWR value.

## Source Precedence

For current-team/status repair, normalized local RotoWire exact deterministic matches are checked before active-pack sidecars. Old checkpoint team remains historical/context only and cannot override RotoWire current team/status.

## Interpretation

- `FA`, blank, unsigned, retired, or equivalent values mean no current team is assigned. The row can be classified as `current_status_verified_no_team` but must not receive an invented team.
- Conflicting current-team sources remain quarantined until reconciled.
- Ambiguous or fuzzy matches are audit candidates only and are not applied repairs.
