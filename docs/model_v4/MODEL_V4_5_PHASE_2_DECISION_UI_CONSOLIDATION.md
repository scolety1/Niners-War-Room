# Model v4.5 Phase 2 - Decision UI Consolidation

## Purpose

Phase 2 addresses the external-audit caution that Model v4's new review-only decision systems were useful but spread across too many Draft Room surfaces.

This phase changes app presentation only. It does not change formulas, generated scores, active rankings, My Team, War Board, readiness gates, app promotion, or final recommendations.

## Draft Room Flow

The Draft Room rookie review area now uses a smaller human-review workflow:

The page now starts with a short "Start here" note that directs the user through internal slot value, owned-pick review, prospect detail, rank explanations, and evidence risk in that order.

1. `Internal Slot`
   - Previously surfaced as Startup Slot Simulator.
   - Compares rookies, picks, roster players, and available context players by internal model value.
   - Still labeled as not ADP and not a final recommendation.
2. `Pick Decision Lab`
   - Keeps owned-pick review front and center.
   - Shows candidate clusters, rookie-vs-player context, risks, and receipts.
3. `Prospect Board`
   - Combines pick windows and the draftable/watchlist/conflict rookie board.
   - Keeps player drilldown available.
4. `Why This Rank`
   - Plain-English explanation layer.
5. `Evidence & Risk`
   - Consolidates supporting context:
     - Evidence Risk
     - Historical Comps
     - Model Edges
6. `Scout / Research`
   - Combines manual scout queue and Deep Research overlay.
7. `Receipts / Warnings`
   - Keeps raw warning and receipt drilldowns available without putting them in the first review path.

## June 15 Flow

The June 15 page now uses clearer decision language:

- A short "Start here" note tells the user to review the Top-Five Drop Decision first, then Pick & Roster Review, then Cut Cost.
- `Cut Opportunity Cost` is displayed as `Cut Cost`.
- `Startup Slot` is displayed as `Internal Slot`.
- The tab remains review-only and explicitly says labels are context, not cut/keep instructions.

## Label Changes

- Startup Slot Simulator -> Internal Slot
- Source Risk Heatmap -> Evidence Risk
- Model Edge Queue -> Model Edges
- Roster Opportunity Cost / Cut Opportunity Cost -> Cut Cost
- Startup Slot -> Internal Slot

Raw output filenames and service names were not changed, so existing scripts and exports remain stable.

## Safety

- No final recommendations were added.
- No active rankings changed.
- No My Team or War Board mutation was added.
- No formula values changed.
- Supporting context remains review-only.

## Verification

Focused checks passed:

- `pytest tests/test_navigation_compression.py -q`
- `ruff check app/pages/06_draft_board.py app/pages/08_june15_review.py tests/test_navigation_compression.py`
- `compileall app/pages/06_draft_board.py app/pages/08_june15_review.py tests/test_navigation_compression.py`
- `Invoke-WebRequest http://127.0.0.1:8502/draft-room`
- `Invoke-WebRequest http://127.0.0.1:8502/decision-board`

Regression coverage now checks that the old top-level Draft Room clutter does not return:

- `Startup Slot Simulator`
- `Scout Queue`
- `Research Overlay`
- `Rookie Warnings`
- `Rookie Receipts`

## Verdict

Decision UI consolidation is implemented. The app should now guide the user through internal slot value, pick decisions, prospect review, explanations, evidence risk, scout context, and receipts in that order.
