# NFLVerse Player Context App Smoke Refresh Summary

Verdict: `GREEN_APP_SMOKE_REFRESH_CLEAN`

## Base

- Branch: `work/nflverse-player-context-app-smoke-refresh-20260630`
- Worktree: `C:\NWR\Niners-War-Room-nflverse-player-context-app-smoke-refresh-20260630`
- Base branch: `origin/work/hq-parallel-control`
- Base HQ HEAD: `096acd4e2d37edb03d3b7091803e2f2f7343204e`

## Purpose

This lane verifies that app surfaces consuming the shared NFLVerse player context artifact pick up the rebuilt review/display-only artifact after approved identity bindings were applied.

No code changes were required.

## Artifact Verified

Tracked artifact:

`docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv`

Observed counts:

- Total player context rows: 294
- Safe display rows: 281
- Remaining gated rows: 13
- Newly activated bound rows: 41
- Newly activated rows verified safe: 41
- Gated rows with exposed detail: 0

## Route Smoke

All requested routes returned HTTP 200 from the Streamlit app shell:

- `/player-compare`
- `/trading-lab`
- `/development-lab`
- `/live-draft-room`
- `/mock-draft`
- `/draft-analyzer`
- `/rankings`
- `/settings-data-health`
- `/refresh-data`

Focused service/page tests verified context behavior for Player Compare, Trading Lab, Development Lab, Draft Cockpit / Live Draft Room, Mock Draft, Draft Analyzer, Injury Availability, Rankings, Data Health, and Refresh Data support code.

## Display Behavior

- Safe rows are eligible for display-only NFLVerse context where the surface already supports it.
- The 41 newly activated rows pass `identity_join_status=SAFE_NOW_DISPLAY_ONLY` and `review_required=false`.
- The 13 gated rows remain fenced as `Not enough information` / `NEED_IDENTITY_REVIEW`.
- Kentrel Bullock and Jamal Haynes remain gated.
- Missing values remain `Not enough information`.
- No row with `review_required=true` exposes NFLVerse identity, schedule, roster, injury, depth, snap, draft, or contract details.

## Decision

The smoke refresh is clean. App surfaces already read the central tracked artifact or shared service layer and pick up the rebuilt counts without code changes.
