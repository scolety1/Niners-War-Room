# Final Verdict

Verdict: `GREEN_AVAILABILITY_DENOMINATOR_DISPLAY_READY`

## Base

- Control branch: `origin/work/hq-parallel-control`
- Merged HQ HEAD after fetch: `13dc684d5173f20230708126b6b82d121cbc3ed0`

## Reason

The merged HQ denominator artifact supports display-only availability denominator
context for safe player-season rows. The service now consumes only the tracked
artifact and schema:

- `docs/hq/data_sources/nflverse_availability_denominator_display_v1_20260630/availability_denominator_display_artifact.csv`
- `docs/hq/data_sources/nflverse_availability_denominator_display_v1_20260630/availability_denominator_schema_manifest.csv`

## Safe Now

Displayed only when the selected player joins by `nwr_player_id`, the player
context identity gate is safe, the denominator row has
`denominator_status=SAFE_NOW_DISPLAY_ONLY`, and the schema allows the field:

- `season_anchor`
- `games_while_rostered`
- `games_with_snaps`
- `games_with_recorded_stats`
- `games_played_context`
- `per_game_denominator`

## Still Blocked

- `games_missed_while_rostered` remains `Not enough information`.
- Identity-review rows expose no denominator detail.
- `NEED_SOURCE_FIELDS` denominator rows expose no denominator detail.
- Schedule next-game, opponent, bye, health, or availability inference remains gated.

## Guardrails

No injury-risk score, medical projection, ACL/comeback projection, durability
score, missing-as-healthy logic, model input, rank logic, source-truth promotion,
hidden sort, recommendation logic, trade value, or pick value was added.
