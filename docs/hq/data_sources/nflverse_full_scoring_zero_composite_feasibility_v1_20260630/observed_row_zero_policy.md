# Observed Row Zero Policy

Explicit zero component rows may be emitted by a future full sidecar builder only when all of these gates pass:

1. The admitted `player_stats_weekly` receipt validates by SHA and row count.
2. The player-week source row exists.
3. The player identity is safe for review/display context.
4. The component source field is present in the admitted schema.
5. The component source field is not quarantined.
6. The component value is explicitly numeric zero.
7. The component is not blocked by composite or special/return touchdown ambiguity.

## Observed Zero Decision

All audited weekly scoring source fields had explicit numeric zero values in observed rows. That supports future explicit zero component rows for observed player-week rows only.

## Blocked Zero Decision

`special_teams_tds` also has explicit zeros, but it remains blocked for full sidecar scoring because it cannot safely populate both NWR `return_td` and `special_td` components without an approved mapping rule.
