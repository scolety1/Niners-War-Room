# Player identity join contract

All historical joins use exactly `player_id`, `season`, and `position`.
Nonblank uniqueness and equal governed identity universes are required.
Player-ID-to-display-name authority is compared across joined sources.

Full-name, normalized-name, partial-name, composed-name, team/position/name,
and mixed-stage fallback joins are rejected before merge. Duplicate or blank
IDs, mismatched universes, swapped IDs, and unchanged display names paired with
changed IDs fail closed. Unresolved identities remain unresolved; no ID is
invented.
