# Scoring Component Gap Report

The sidecar includes observed nonzero rows for safe direct scoring components and explicit observed-zero rows for the three composite blocker components: `fumbles_lost`, `return_yards`, and `return_or_special_touchdowns`.

## Remaining gaps

- Direct zero expansion for every component is not present in compact V1.
- Missing player-week rows remain `Not enough information`, never zero.
- `return_touchdowns` and `special_touchdowns` are blocked as direct components.
- The sidecar uses a single composite `return_or_special_touchdowns` component under the approved 4-point single-count policy.
- Quarantined fields, including `fantasy_points` and EPA/CPOE/share-style fields, remain excluded.

These gaps block global scoring parity and label-truth promotion.
