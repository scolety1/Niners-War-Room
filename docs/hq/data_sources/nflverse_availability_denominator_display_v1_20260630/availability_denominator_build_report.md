# Availability Denominator Build Report

Verdict: YELLOW_PARTIAL_DENOMINATOR_ARTIFACT_READY

## Counts

- Source player context rows: 294
- Artifact rows: 588
- Season anchors: 2 (`2024`, `2025`)
- `SAFE_NOW_DISPLAY_ONLY` player-season rows: 437
- `NEED_SOURCE_FIELDS` player-season rows: 43
- `NEED_IDENTITY_APPROVAL` player-season rows: 108
- Rows with `games_with_snaps` populated: 429
- Rows with `games_with_recorded_stats` populated: 429

## Fields Built

- `games_while_rostered`: built for safe identity rows with a regular-season `weekly_rosters` plus `schedules` join.
- `games_with_snaps`: populated only when positive recorded snap rows exist.
- `games_with_recorded_stats`: populated only when weekly stat rows exist.
- `games_played_context`: display-only context string; not a played/missed/health inference.
- `per_game_denominator`: equal to `games_while_rostered` only when that denominator is supportable.
- `season_anchor`: dynamic row anchor for 2024 and 2025.

## Fields Still Blocked

- `games_missed_while_rostered`: blocked because the current approved sources do not provide a safe game-status denominator that distinguishes missed games from missing snap/stat rows.

## Source Caveats

- Postseason rows are excluded from denominator counts.
- Identity-review rows are included only as blocked review rows and expose no denominator detail.
- A row with no weekly roster/schedule join remains `Not enough information`; it is not a zero-game row.
