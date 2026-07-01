# Blocked Components Report

## Still blocked

| Component | Status | Reason |
| --- | --- | --- |
| Direct `return_touchdowns` | Blocked | No direct `return_tds` field is approved/present. |
| Direct `special_touchdowns` | Blocked | No separate `special_tds` field is approved/present. |
| Return-vs-special TD subtype parity | Blocked | `special_teams_tds` is counted once as composite `return_or_special_touchdowns`; subtype cannot be inferred. |
| Direct zero expansion for all formula components | Blocked in compact V1 | Would require a much larger zero-expanded artifact. Omitted direct zero rows are not misses and not zero in downstream joins. |
| Global scoring parity | Blocked | Missing player-week rows remain `Not enough information`. |
| Quarantined fields | Blocked | `fantasy_points`, `fantasy_points_ppr`, EPA/CPOE/share-style fields, and display/headshot fields excluded. |

## Resolved for observed rows

- `fumbles_lost` is derived once from `sack_fumbles_lost + rushing_fumbles_lost + receiving_fumbles_lost`.
- `return_yards` is derived once from `kickoff_return_yards + punt_return_yards`.
- `special_teams_tds` is mapped once to `return_or_special_touchdowns` for point-total component review.
