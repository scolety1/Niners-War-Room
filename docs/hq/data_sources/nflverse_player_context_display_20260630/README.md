# NFLVerse Player Context Display Artifact

Verdict: `YELLOW_PARTIAL_PLAYER_CONTEXT_ARTIFACT`
Current Rankings rows evaluated: `294`

This directory contains compact, derived, review/display-only player context from the approved local nflverse refresh-health contract. It is not raw cache.

## Artifact Grain

- Primary app artifact: one row per current NWR Rankings/unified-board player.
- Join-health support: one row per gate/dataset, used to explain coverage and deferred fields.
- No broad observed-nflverse-player artifact is approved in this lane.

## App-Lane Consumption Contract

App lanes may read `nflverse_player_context_display_artifact.csv` and `nflverse_player_context_join_health.csv` as display context only. They must not read raw `C:\NWR_SHARED_DATA` nflverse files directly.

- Join on `nwr_player_id` only.
- Required row filter for player-level use: `identity_join_status=SAFE_NOW_DISPLAY_ONLY` and `review_required=false`.
- Confirm the relevant field has `field_status=SAFE_NOW_DISPLAY_ONLY` in `nflverse_player_context_schema_manifest.csv` before showing it.
- Treat `Not enough information`, `NEED_DATASET_REFRESH`, `NEED_IDENTITY_REVIEW`, `NEED_SCHEMA_REVIEW`, `BLOCKED_SOURCE_POLICY`, and `BLOCKED_VENDOR_OR_PRIVATE` as unavailable display values.
- Every row remains `display_only=true` with model/training/source-truth/rank/hidden-sort/trade/pick flags set to `false`.

## Safe Display Fields Now

- Identity/profile: `nflverse_gsis_id`, `nflverse_sleeper_id`, `nflverse_player_name`, `nflverse_team`, `nflverse_position` after the required identity filter.
- Roster/age: `roster_birth_date_derived_age`, `age_source`, `roster_status`, `weekly_roster_status`.
- Review/status context: `injury_report_status`, `injury_report_date_week`, `practice_status`, `depth_chart_position`, `depth_chart_rank`, `depth_chart_role`, `snap_count_recency`, `latest_snap_season`, `latest_snap_week`, `snap_sample_size`, `last_active_season`, `last_active_week`, `draft_year`, `draft_round`, `draft_pick`, `drafted_team`, non-financial `contract_context`, `next_game_context`, `opponent_context`, and `bye_context`, only when values are present and not gate tokens.

## Deferred Or Blocked

- `ff_rankings` is blocked and unused.
- Schedule fields are display-only and require current/future approved schedules. If a row still says `Not enough information`, app lanes must not infer an opponent, bye, or clean schedule state.
- Rows with `identity_join_status=NEED_IDENTITY_REVIEW` need separate identity review before any player-level app display.