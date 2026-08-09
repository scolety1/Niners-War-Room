# Redraft Ranking Contract

1. Validate the league profile and current-season projection schema.
2. Score granular projected stats under the exact profile.
3. Fill mandatory starters, then FLEX and SUPERFLEX by marginal projected points.
4. Simulate bounded bench demand and identify the best unrostered positional replacement.
5. Rank by projected points minus replacement points using `R2_FLEX_AWARE_REPLACEMENT`.
6. Break ties by projected points, position, then stable player ID.
7. Build deterministic tiers from robust adjacent value gaps and expose source/confidence status.

K/DST are supported only when a governed `projected_points_override` is supplied. Unsupported
bonuses fail validation. Operational snapshots require admitted statuses, a maximum 30-day-old ISO
`source_as_of`, minimum positional depth, a separately issued NWR Data Governance receipt that
binds the source SHA, and a matching runtime manifest. Missing player evidence is blocked, not
scored as zero. Player Compare requires an exact stable player ID.
