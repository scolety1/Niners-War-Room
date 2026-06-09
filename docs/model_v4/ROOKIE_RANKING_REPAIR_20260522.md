# Rookie Ranking Repair - 2026-05-22

## Why This Patch Exists

Two pro audits returned the same concern:

- the rookie ranking formula let low-evidence players rank too high;
- the Prospect Board mixed draftable candidates with watchlist/data-incomplete rows;
- the UI did not show enough source context to explain a prospect score.

This patch repairs the guardrails without promoting active rankings, changing My Team, changing War Board, or creating final rookie recommendations.

## Formula Guardrails Added

Sprint 14E rookie review now:

- multiplies league-format adjusted rookie score by `component_weight_available`;
- caps low-evidence rows with `component_weight_available < 0.50`;
- assigns explicit `evidence_status`:
  - `draftable_review`
  - `manual_scout_source_review`
  - `watchlist_data_incomplete`
- moves low-evidence rows into `watchlist_or_data_incomplete_context_review`;
- moves identity/source-review rows into `manual_scout_context_review`;
- excludes `watchlist_data_incomplete` rows from ordinary pick-candidate windows.

## Key Outcome

The suspicious examples are now demoted:

- Daniel Sobkowicz moved from rank 1 to watchlist/data-incomplete.
- Mike Washington moved to watchlist/data-incomplete.
- Ty Thompson moved to watchlist/data-incomplete.

High-evidence rows still remain review-only, and some important players remain in manual scout status when source/identity warnings are present.

## UI Repair

The Draft Room Prospect Board now splits into:

- Draftable Board
- Manual Scout
- Watchlist / Data Incomplete
- Research Conflicts

The board also exposes more score ingredients:

- Evidence Available
- Row Status
- Production
- Market Share
- Athletic
- Recruiting
- Landing Context
- Research Tier
- Research Stance

## Remaining Known Issue

The audits also found that some high-priority research names, especially Carnell Tate, Jadarian Price, and Kenyon Sadiq, may still be undervalued by the underlying prospect model. That should be handled in a separate formula pass because draft-capital and market-context rules need careful source-lane treatment.

Deep Research remains review-only context and does not drive private football value.

## Verification

- Focused tests passed: `30 passed`
- Ruff passed on touched files
- Sprint 14E outputs regenerated
