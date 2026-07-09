# Model v4 Regeneration Identity and Missingness Rules

## Identity Rules

- Canonical player IDs are required where available.
- Name-only joins are blocked.
- Player-season-position keys must be unique.
- Position must be season-aligned, not copied blindly from current board state.
- Duplicate keys must stop regeneration unless resolved in a review artifact.
- Cross-source joins must record source artifact, source hash, and join fields.

## Required Key Fields

- `season`
- `position`
- `canonical_player_key` or stable `player_id`
- `player_name`
- `source_artifact`
- `source_sha256`

## Missingness Policy

Every generated receipt row must distinguish:

- `true_zero`: the source exists and confirms zero.
- `unknown`: the source does not provide the value.
- `missing_source`: source artifact absent.
- `not_applicable`: field is structurally irrelevant for the player/position.
- `blocked_source`: source exists but is not admitted for this use.

## Sparse-History Policy

Rows must include flags when a player has sparse history, low games, rookie/second-year status if available, or incomplete prior-season context. Missingness can be used as review context, not as production approval.

## Validation Checks

- Unique key check.
- Duplicate player-name collision check.
- Null/blank key check.
- Position coverage by season.
- Missingness count by family and source.
- True-zero vs unknown audit.
- Identity caveat summary.
