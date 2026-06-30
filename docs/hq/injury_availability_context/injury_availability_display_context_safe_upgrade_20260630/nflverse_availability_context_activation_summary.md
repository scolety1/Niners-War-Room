# NFLVerse Availability Context Activation Summary

Verdict: `YELLOW_PARTIAL_AVAILABILITY_CONTEXT_GATED`

Date: 2026-06-30

## Source Of Truth

This rerun consumes only tracked repo artifacts:

- `docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv`
- `docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_schema_manifest.csv`
- `docs/hq/data_sources/nflverse_dataset_level_refresh_health_20260630/`

No app page reads raw `C:\NWR_SHARED_DATA` NFLVerse cache for this display.

## Coverage Consumed

- Player context artifact rows: `294`
- Safe display rows: `240`
- Identity review rows: `54`
- Identity proposals: `43`, proposals only
- Human-review identity rows: `4`
- `KEEP_NEED_IDENTITY_REVIEW`: `7`
- Schedule current/future next-game/opponent/bye display: gated for a separate lane-specific activation review
- `ff_rankings`: blocked and unused

## Moved From WAIT To SAFE_NOW

The following fields moved from prior waiting status to implemented display-only context,
but only when `identity_join_status=SAFE_NOW_DISPLAY_ONLY`,
`review_required=false`, and the schema manifest marks the field
`SAFE_NOW_DISPLAY_ONLY`:

- roster status
- weekly roster status
- injury report status
- practice status
- injury report date/week/as-of context
- last active season/week
- snap recency
- snap sample size
- age and age source
- identity join status and identity caveat
- player-level availability context present/unavailable label

## Still Deferred

- `games_while_rostered`
- `games_with_snaps`
- `games_with_recorded_stats`
- `games_missed_while_rostered`
- `per_game_denominator`
- dynamic season anchors
- current/future next-game, opponent, and bye display

These remain deferred because the tracked artifact does not provide approved
per-game denominator fields or current/future schedule values.

## UI Activation

Player Compare now shows a tracked-artifact NFLVerse Availability Context table
inside the existing Injury / Availability panel. Rankings already shows NFLVerse
context in Data Review and dataset status in the refresh/status expander.

All displayed values are display-only/review-only and do not affect rank, tier,
model value, hidden sort, trade value, pick value, or recommendations.
