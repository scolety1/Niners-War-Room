# NFLVerse Schedule Context Display Follow-up

Verdict: `YELLOW_SCHEDULE_CONTEXT_PARTIAL_SURFACES`

## Base

- Base branch: `origin/work/hq-parallel-control`
- Base HQ HEAD: `3b45aa6dbe562368127f6ce8c72a36ba4dbe6d59`
- Worktree: `C:\NWR\Niners-War-Room-nflverse-schedule-context-display-followup-20260630`
- Branch: `work/nflverse-schedule-context-display-followup-20260630`

## Inputs Confirmed

- Schedule gate artifacts: `docs/hq/data_sources/nflverse_schedule_context_display_gate_v1_20260630/`
- Player context display artifact: `docs/hq/data_sources/nflverse_player_context_display_20260630/`
- Player context hardening artifacts: `docs/hq/data_sources/nflverse_player_context_hardening_20260630/`

The schedule gate confirms 294 player-context rows, 240 safe display rows, 54 identity-review rows, and 0 gated rows with populated schedule context.

## Implementation

- Added `src/services/nflverse_schedule_context_display_service.py` as the shared gate helper for schedule display.
- The helper reads only tracked repo artifacts, joins by `nwr_player_id`, requires `identity_join_status=SAFE_NOW_DISPLAY_ONLY`, `review_required=false`, schema-safe schedule fields, and all display-only guardrail flags.
- Draft Cockpit, Mock Drafts, and Draft Analyzer now show safe schedule context through the existing NFLVerse player-context expander.
- Development Lab now shows safe schedule context rows in status, roster, draft-prep, and deadline review panels.
- Player Compare already showed safe schedule context and remains unchanged.
- Trading Lab remains gated; copy now says the schedule surface is pending Trading Lab-specific display review rather than claiming no current/future schedule rows exist.
- Injury / Availability remains gated for next-game/opponent/bye display because of health/availability inference risk.

## Display Scope

Allowed display fields are factual only: `next_game_context`, `opponent_context`, `bye_context`, parsed `game_date`, `game_week`, `home_away`, `season`, and `team`.

No rank, tier, model, source-truth, hidden sort, recommendation, injury risk, medical projection, trade value, pick value, draft runtime state, or event-log behavior changed.
