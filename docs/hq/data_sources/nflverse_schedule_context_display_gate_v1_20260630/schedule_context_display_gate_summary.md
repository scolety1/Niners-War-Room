# NFLVerse Schedule Context Display Gate Summary

Final gate verdict: `YELLOW_SCHEDULE_CONTEXT_PARTIAL_LANE_GATING`

## Base

- Base branch: `origin/work/hq-parallel-control`
- Base HEAD: `29e1d31514b2e64e124cc703b8b966f65409beb6`

## Schedule Source Artifacts Found

- `docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv`
- `docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_build_report.md`
- `docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_schema_manifest.csv`
- `docs/hq/data_sources/nflverse_player_context_hardening_20260630/schedule_future_coverage_audit.md`
- `docs/hq/data_sources/nflverse_player_context_hardening_20260630/APP_LANE_CONSUMPTION_GUIDE_20260630.md`
- `docs/hq/data_sources/nflverse_player_context_schedule_audit_20260630/nflverse_schedule_context_audit.csv`
- `docs/hq/data_sources/nflverse_player_context_schedule_audit_20260630/nflverse_schedule_context_build_report.md`
- `docs/hq/data_sources/nflverse_dataset_level_refresh_health_20260630/nflverse_dataset_registry_v1.csv`

## Current Safe Schedule Artifact

The tracked artifact with safe schedule context is:

`docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv`

Row grain: one row per current NWR player / current Rankings universe player.

## Coverage

- Player context artifact rows: `294`
- Rows passing `identity_join_status=SAFE_NOW_DISPLAY_ONLY` and `review_required=false`: `240`
- Identity-review / gated rows: `54`
- Safe rows with populated `next_game_context`: `240`
- Safe rows with populated `opponent_context`: `240`
- Safe rows with populated `bye_context`: `240`
- Gated rows with populated schedule context: `0`

The older schedule audit found 2024-2025 schedules only, 34 teams audited, 32 teams with schedule rows, and 0 current/future games as of 2026-06-30. The later hardening packet documents the approved targeted 2026 schedules refresh: 272 schedule rows, 2026 season, weeks 1-18, max game date 2027-01-10, 32 teams covered.

## Safe Rows

Schedule context is safe to expose only for rows that pass all of:

- `identity_join_status=SAFE_NOW_DISPLAY_ONLY`
- `review_required=false`
- requested schedule field is not `Not enough information`
- consuming lane treats the field as display-only/review-only

## Blocked / Gated Rows

Rows with `identity_join_status=NEED_IDENTITY_REVIEW`, `review_required=true`, missing `nwr_player_id`, missing schedule fields, stale schedule status, or any source-policy mismatch must show `Not enough information` or remain hidden behind the lane's unavailable/missing-evidence copy.

## Gate Decision

Schedule context is source-policy approved for factual display on existing safe player-context rows. It is not approved for model input, rank logic, hidden sort, recommendations, matchup strength, start/sit, injury-risk, trade value, pick value, or Outcome probability changes.

Some app lanes already have safe-row schedule display. Others intentionally kept schedule context gated before the 2026 hardening overlay existed; those lanes need lane-specific review/tests before UI behavior changes. That is why the central verdict is partial lane gating rather than blanket green.
