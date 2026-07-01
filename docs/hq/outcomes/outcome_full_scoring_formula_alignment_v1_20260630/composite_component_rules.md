# Composite Component Rules

## Fumbles lost

A future observed-row builder may derive `fumbles_lost` as:

`coalesce(sack_fumbles_lost, 0) + coalesce(rushing_fumbles_lost, 0) + coalesce(receiving_fumbles_lost, 0)`

Only within an observed player-week row where the source columns are present. Missing player-week rows are not zero.

## Return yards

A future observed-row builder may derive `return_yards` as:

`coalesce(kickoff_return_yards, 0) + coalesce(punt_return_yards, 0)`

Only within an observed player-week row where the source columns are present. Missing player-week rows are not zero.

## Special / return touchdowns

A future observed-row builder may derive `return_or_special_touchdowns` from `special_teams_tds` and count it once at 4 points. It may not populate both return and special touchdown components from the same source value.

## Zero-row boundary

These composite rules do not authorize global zero-fill. They operate only inside observed source rows. A separate zero-row completeness gate is required before missing rows can be interpreted as zero.
