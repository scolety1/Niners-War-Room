# Trading Lab Schedule Context Activation Review

Date: 2026-06-30

Branch: `work/trading-lab-schedule-context-review-20260630`

Base HQ HEAD: `f1ee976042724911ae7dc5ffac5f5b12e4b30b2a`

## Decision

Trading Lab can safely display NFLVerse schedule context for selected manual-planner player assets when the row passes the merged schedule display gate.

Verdict: `GREEN_TRADING_LAB_SCHEDULE_CONTEXT_DISPLAY_READY`

## Why This Is Safe

The implementation reuses `src/services/nflverse_schedule_context_display_service.py`, which reads only tracked repo artifacts and applies the central schedule display gate:

- join by `nwr_player_id`
- `identity_join_status=SAFE_NOW_DISPLAY_ONLY`
- `review_required=false`
- schema field status is `SAFE_NOW_DISPLAY_ONLY`
- display-only is true
- model, training, source-truth, rank, hidden-sort, trade-value, and pick-value flags are false

Trading Lab adds schedule detail only to the existing NFLVerse context table. It does not write schedule data into planner state, calculate package totals, change ranks, change source truth, or create recommendations.

## Implemented Display Fields

- `next_game_context`
- `opponent_context`
- `bye_context`
- `game_date`
- `game_week`
- `home_away`
- `season`
- `team`

All schedule rows are labeled:

- Display-only
- Manual review only
- Not model input
- No valuation calculated
- No automatic recommendation

## Current Coverage From Gate

- Artifact rows: 294
- Safe schedule rows: 240
- Identity-review rows: 54
- Safe next-game rows: 240
- Safe opponent rows: 240
- Safe bye rows: 240

## Trading Lab Behavior

- Safe player rows show factual schedule context.
- Identity-review rows expose no schedule detail.
- Pick/context assets show no schedule context.
- Missing or gated schedule context displays `Not enough information`.
- Manual memo/export keeps the no-valuation disclaimer.

## No-Go Confirmation

This lane did not add trade timing advice, matchup recommendations, buy/sell/hold language, start/sit, schedule strength, playoff odds, opponent difficulty, market/ADP/KTC/DynastyProcess logic, automatic trade finder, offer generator, package fairness, trade value delta, pick value, injury risk, medical projection, health inference, model score, hidden sort, or rank/source-truth changes.
