# Zero Composite Feasibility Summary

Verdict: `YELLOW_ZERO_COMPOSITE_FEASIBILITY_PARTIAL_BLOCKERS`

## Executive Decision

Explicit zero component rows are feasible for observed `player_stats_weekly` source rows when the source field exists and contains an explicit numeric zero. Missing player-week rows are not zero and must remain `Not enough information`.

Composite components are partially feasible:

- `fumbles_lost` can be review-derived for observed player-week rows from `rushing_fumbles_lost + receiving_fumbles_lost + sack_fumbles_lost`.
- `return_yards` can be review-derived for observed player-week rows from `kickoff_return_yards + punt_return_yards`.
- `return_touchdowns` and `special_touchdowns` remain blocked because `special_teams_tds` is present but does not safely distinguish return TDs from other special teams TDs for the two separate NWR formula components.

## Local Source Validation

The admitted local-only snapshot was read only for aggregate feasibility checks. No raw rows or raw files were copied into git.

- Weekly rows observed: `76804`
- Weekly receipt SHA matched: `true`
- Seasonal rows observed: `42419`
- Seasonal receipt SHA matched: `true`

## Zero Row Decision

Future full sidecar builder may emit explicit zero rows only at this grain:

`observed_source_row + safe_identity + review_allowed_field + explicit_numeric_zero`

The builder must not emit zero rows for:

- missing player-week source rows;
- players absent from player_stats;
- identity-review rows;
- rostered-but-unobserved rows;
- schedule/roster inferred rows without a separate approved gate.

## Remaining Blockers

- Special/return touchdown split remains blocked.
- Missing player-week rows remain `Not enough information`.
- This packet does not approve full scoring sidecar construction by itself.
- Label truth, model, training, and source truth remain closed.
