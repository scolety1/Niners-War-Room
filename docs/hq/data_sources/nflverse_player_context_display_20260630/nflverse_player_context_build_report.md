# NFLVerse Player Context Build Report

Verdict: `YELLOW_PARTIAL_REBUILD_WITH_GATED_ROWS`
Current Rankings source: `current_unified_rankings; dynasty=approved control-repo dynasty rankings; frozen=local frozen board`
Current Rankings rows: `294`
Artifact rows: `294`
Safe refresh attempted: `true`
Safe refresh status: `succeeded: approved scripts/run_nflverse_refresh_v0.ps1 schedules-only 2026 overlay player_context_hardening_schedule_20260630`

## Dataset Inspection

| dataset | status | rows | coverage | freshness | policy | usability | local path |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| players | GREEN | 25033 | seasons=1974-2025 | fresh | identity_only | SAFE_NOW_DISPLAY_ONLY | C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\player_context_display_final_20260630\players.csv |
| rosters | YELLOW | 6353 | seasons=2024-2025; weeks=22 | fresh | identity_only | SAFE_NOW_DISPLAY_ONLY | C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\player_context_display_final_20260630\rosters.csv |
| weekly_rosters | YELLOW | 93428 | seasons=2024-2025; weeks=22 | fresh | identity_only | SAFE_NOW_DISPLAY_ONLY | C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\player_context_display_final_20260630\weekly_rosters.csv |
| ff_playerids | YELLOW | 12465 | seasons=1970-2026 | fresh | identity_only | SAFE_NOW_DISPLAY_ONLY | C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\player_context_display_final_20260630\ff_playerids.csv |
| injuries | YELLOW | 12283 | seasons=2024-2025; weeks=22 | fresh | transparency_only | SAFE_NOW_DISPLAY_ONLY | C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\player_context_display_final_20260630\injuries.csv |
| schedules | YELLOW | 272 | seasons=2026; weeks=18 | fresh | display_only | SAFE_NOW_DISPLAY_ONLY | C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\player_context_hardening_schedule_20260630\schedules.csv |
| depth_charts | YELLOW | 591527 | seasons=2024; weeks=22 | fresh | review_only | SAFE_NOW_DISPLAY_ONLY | C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\player_context_display_final_20260630\depth_charts.csv |
| snap_counts | YELLOW | 53227 | seasons=2024-2025; weeks=22 | fresh | safe_review | SAFE_NOW_DISPLAY_ONLY | C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\player_context_display_final_20260630\snap_counts.csv |
| player_stats_weekly | YELLOW | 76804 | seasons=2024-2025; weeks=22 | fresh | safe_review | SAFE_NOW_DISPLAY_ONLY | C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\player_context_display_final_20260630\player_stats_weekly.csv |
| player_stats_seasonal | GREEN | 42419 | seasons=2024-2025; weeks=22 | fresh | safe_review | SAFE_NOW_DISPLAY_ONLY | C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\player_context_display_final_20260630\player_stats_seasonal.csv |
| draft_picks | GREEN | 514 | seasons=2024-2025 | fresh | safe_review | SAFE_NOW_DISPLAY_ONLY | C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\player_context_display_final_20260630\draft_picks.csv |
| combine | GREEN | 650 | seasons=2024-2025 | fresh | safe_review | SAFE_NOW_DISPLAY_ONLY | C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\player_context_display_final_20260630\combine.csv |
| contracts | YELLOW | 51672 | seasons=1983-2026 | fresh | display_only | SAFE_NOW_DISPLAY_ONLY | C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\player_context_display_final_20260630\contracts.csv |
| teams | GREEN | 36 | seasons=Not enough information | fresh | display_only | SAFE_NOW_DISPLAY_ONLY | C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\player_context_display_final_20260630\teams.csv |
| ff_rankings | BLOCKED | Not enough information | Not enough information | not_applicable | blocked_policy | BLOCKED_VENDOR_OR_PRIVATE | Not enough information |

## Approved Identity Binding Apply - 2026-06-30

Source binding packet: `docs/hq/data_sources/nflverse_approved_identity_nwr_binding_v1_20260630/approved_identity_nwr_binding_matrix.csv`

| Metric | Count |
| --- | ---: |
| Previously safe display rows | 240 |
| Approved/bound rows applied | 41 |
| Safe display rows after apply | 281 |
| Remaining identity-review/gated rows | 13 |
| Non-approved or unbound rows exposed as safe context | 0 |

No raw shared-cache refresh was run in this apply. Newly bound rows received approved NWR/Sleeper/GSIS identity fields only; unavailable context fields remain `Not enough information`.
