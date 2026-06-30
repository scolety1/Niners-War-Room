# Trading Lab NFLVerse Context Activation Summary

Date: 2026-06-30

Branch: work/lane-trading-lab-nflverse-context-20260630

Base: origin/work/hq-parallel-control at 2070a2f4ffa6b6ae83bd6ca1529880f67dd6cab0

## Purpose

Trading Lab now displays factual NFLVerse player context inside the manual planner workflow when the approved player context artifact supports it.

This is display-only context for human review. It is not a trade calculator, offer generator, pick valuation layer, player valuation layer, hidden sort field, ranking source, or recommendation engine.

## Source Used

Tracked source:

`docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv`

Supporting schema:

`docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_schema_manifest.csv`

The app page does not read raw `C:\NWR_SHARED_DATA` NFLVerse data. It reads the tracked HQ display artifact through a Trading Lab display-only service.

## Artifact Coverage

- Player context artifact rows: 294
- Safe display rows: 240
- Identity review rows: 54
- Identity proposals: 43 proposals exist in the upstream review packet, but they are proposals only and are not treated as approved joins.
- Schedule next game, opponent, and bye context: activated later by the Trading Lab schedule context review for rows passing the shared schedule display gate.

## Display Rules

NFLVerse context appears only when:

- `identity_join_status` is `SAFE_NOW_DISPLAY_ONLY`
- `review_required` is `false`
- the schema marks the field as `SAFE_NOW_DISPLAY_ONLY`
- display-only is true
- model, training, source-truth, rank, hidden-sort, trade-value, and pick-value use are all false

Rows with `NEED_IDENTITY_REVIEW` show identity-review status only. Player context details are hidden.

The frozen board and existing Trading Lab lane props do not consistently carry `nwr_player_id`. Where the selected board row lacks an ID, Trading Lab resolves the row to the tracked artifact's approved NWR player ID only through a unique visible identity match from the artifact, then displays details from the artifact row. Manual planner rows can also use an explicit NWR Player ID entered by the user.

## Context Groups Activated

- Identity Context
- Availability Context
- Role Context
- Production / Activity Context
- Draft Context
- Contract Context, non-financial only
- Missing Evidence Panel

Every context card includes:

- Display-only context
- Manual review only
- No valuation calculated
- No automatic recommendation
- Source/as-of/freshness labels where available

Missing values render as exactly `Not enough information`.

## Deferred

- Identity-review schedule details
- Identity proposal rows
- Any `NEED_*`, `BLOCKED_*`, `Review needed`, or `Not enough information` value as a positive fact
- `ff_rankings`
- Medical projection or injury-risk scoring
- Role, opportunity, confidence, trade, pick, package, market, ADP, DynastyProcess, or KTC valuation

## Verdict

GREEN for display-only NFLVerse context activation, pending the final command-level validation report in `test_report.md`.
