# Quarantined Or Missing Scoring Fields

## Quarantined Fields

The source-admission packet quarantines these fields and they remain excluded from any review sidecar:

- `air_yards_share`
- `fantasy_points`
- `fantasy_points_ppr`
- `headshot_url`
- `pacr`
- `passing_cpoe`
- `passing_epa`
- `racr`
- `receiving_epa`
- `rushing_epa`
- `target_share`
- `wopr`

`fantasy_points` and `fantasy_points_ppr` must not be used to validate NWR scoring parity because they are imported scoring totals rather than raw component evidence.

## Missing Or Ambiguous Scoring Fields

- Direct `return_tds` is not present.
- Direct `fumbles_lost` is not present as a single field.
- `special_teams_tds` is present but ambiguous for separating NWR `return_td` and `special_td`.

## Composite Fields That Need Builder Rules

- `fumbles_lost` may be review-derived from `rushing_fumbles_lost + receiving_fumbles_lost + sack_fumbles_lost` for observed player-week rows only.
- `return_yards` may be review-derived from `kickoff_return_yards + punt_return_yards` for observed player-week rows only.

## Zero Handling

Explicit zero component rows may be emitted only from observed source rows with explicit numeric zero component values. Missing source rows, missing identities, missing roster evidence, and missing schedules remain `Not enough information`.
