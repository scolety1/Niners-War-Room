# Stable Identity Blocker Revalidation

## Controlling result

`BLOCKED_ROSTER_HYDRATION_STABLE_IDENTITY_NOT_AVAILABLE`

The only admissible player join is:

`Sleeper player ID` -> `dim_players.sleeper_id` -> canonical NWR `player_id`

The tracked clean-checkout fixture contains 24 `dim_players` rows, 24 unique canonical player IDs, and zero nonblank `sleeper_id` values. Its 24 roster rows have unique synthetic NWR player IDs and join to the synthetic dimension, but this proves only fixture-internal NWR identity. It proves no Sleeper-to-NWR mapping.

No tracked artifact proves complete, unique, stable coverage for the intended admitted-roster join. Duplicate, ambiguous, blank, inactive/retired, kicker, DST, and draft-pick coverage are not established for production roster scope.

The following remain prohibited, including after an exact-ID lookup fails:

- player name;
- normalized name;
- name/team/position composite;
- rank/name/position composite;
- display-field hashing;
- inferred opaque identifiers.

One unresolved identity makes coverage partial. A duplicate source or canonical identity invalidates aggregate calculation. No row may be silently omitted or repaired by fallback.
