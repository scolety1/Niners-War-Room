# NFLVerse Availability Context Activation Summary

Verdict: `GREEN_AVAILABILITY_DENOMINATOR_DISPLAY_READY`

Date: 2026-06-30

## Source Of Truth

This follow-up consumes only tracked repo artifacts from merged HQ HEAD
`13dc684d5173f20230708126b6b82d121cbc3ed0`:

- `docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv`
- `docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_schema_manifest.csv`
- `docs/hq/data_sources/nflverse_availability_denominator_display_v1_20260630/availability_denominator_display_artifact.csv`
- `docs/hq/data_sources/nflverse_availability_denominator_display_v1_20260630/availability_denominator_schema_manifest.csv`
- `docs/hq/data_sources/nflverse_schedule_context_display_gate_v1_20260630/`
- `docs/hq/data_sources/nflverse_player_context_identity_approval_v1_20260630/`

No app page reads raw `C:\NWR_SHARED_DATA` NFLVerse cache for this display.

## Coverage Consumed

- Player context artifact rows: `294`
- Safe player display rows: `240`
- Player identity-review rows: `54`
- Denominator artifact rows: `588`
- Safe denominator player-season rows: `437`
- Denominator rows gated by source fields: `43`
- Denominator rows gated by identity approval: `108`
- `games_missed_while_rostered` populated rows: `0`
- `ff_rankings`: blocked and unused

## Moved From WAIT To SAFE_NOW

The following fields moved from prior gated status to implemented
display-only context, only for safe identity rows and
`denominator_status=SAFE_NOW_DISPLAY_ONLY` rows:

- `season_anchor`
- `games_while_rostered`
- `games_with_snaps`
- `games_with_recorded_stats`
- `games_played_context`
- `per_game_denominator`

The previously activated direct player-context fields remain display-only:

- roster status
- weekly roster status
- injury report status
- practice status
- injury report date/week/as-of context
- last active season/week
- snap recency and sample size
- age and age source
- identity join status and identity caveat

## Still Deferred

- `games_missed_while_rostered`: blocked until an explicit game-status source
  distinguishes missed games from missing snap/stat rows.
- Identity-review rows: status-only; no detailed NFLVerse denominator context.
- Identity recommendations: proposals only, not approved joins.
- Schedule next-game, opponent, bye, health, or availability inference: gated
  for lane-specific activation review.

## UI Activation

Player Compare renders denominator context through the existing
`NFLVerse Availability Context` table. The page does not compute denominators
and does not read raw shared NFLVerse data.

All displayed values are display-only/review-only and do not affect rank, tier,
model value, hidden sort, trade value, pick value, Outcome probability, or
recommendations.
