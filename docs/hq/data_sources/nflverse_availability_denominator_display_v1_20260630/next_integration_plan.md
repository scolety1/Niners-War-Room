# Next Integration Plan

## Recommended App Integration Lane

A future app lane may read `availability_denominator_display_artifact.csv` as a tracked, compact, review/display-only artifact.

## Required App Filters

- Join by `nwr_player_id` only.
- Require `identity_join_status=SAFE_NOW_DISPLAY_ONLY`.
- Require `review_required=false`.
- Require `denominator_status=SAFE_NOW_DISPLAY_ONLY` before showing numeric denominator context.
- Treat `Not enough information` as missing, not zero/healthy/clean/no-role.

## Safe Display Fields

- `season_anchor`
- `games_while_rostered`
- `games_with_snaps` when populated
- `games_with_recorded_stats` when populated
- `games_played_context`
- `per_game_denominator`
- `coverage_status`
- `missing_reason`

## Keep Deferred

- `games_missed_while_rostered` until an explicit game-status source gate exists.
- Any injury-risk, medical, durability, comeback, recommendation, rank, model, hidden-sort, trade-value, or pick-value use.

## Raw Data Rule

App pages must not read `C:\NWR_SHARED_DATA` directly. They may only consume the tracked display artifact after this packet is reviewed/merged.
