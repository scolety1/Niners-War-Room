# Model v4.5 External Audit Prompt

You are auditing Model v4.5, a local-first dynasty fantasy football decision model for a 10-team, 1QB, non-PPR, first-down scoring league with no TE premium.

The goal is to determine whether the v4.5 cleanup sprint resolved prior audit cautions and whether the system is ready for human final decision review. Do not judge it by whether it matches consensus rankings. Weird model outputs are acceptable if they are supported by admitted evidence and clearly labeled.

## Context

- All outputs must remain review-only.
- No active rankings, My Team, War Board, readiness gates, or app promotion should be mutated.
- No final cut/keep/trade/draft recommendations should be created.
- Market, ADP, rankings, projections, mock drafts, big boards, and consensus cannot drive private football value.
- Missing data must remain missing.
- Historical outcomes, comps, and model-edge context are display/review context only.

## Audit Tasks

1. Review the five v4.5 phase docs and final readiness page.
2. Verify whether the Phase 1 guard/admission validation repair is sufficient:
   - factual rookie age admitted only through approved source/lane
   - factual NFL draft capital admitted only through approved source/lane
   - market/rank/projection/mock/big-board/consensus fields remain blocked
3. Verify whether the Phase 2 UI consolidation makes the review workflow understandable.
4. Verify whether the Phase 3 explainer de-dupe strategy removes confusing duplicate rows while preserving alternate-context receipts/warnings.
5. Verify whether Phase 4 safely handles 2026 5.04:
   - no synthetic baseline created
   - numeric fields remain blank
   - `manual_only_no_exact_model_baseline` is visible
   - exact trade/draft/cut equivalence is blocked
6. Verify whether Phase 5 naming/warning cleanup is human-readable:
   - default tables use clean labels
   - warning groups are understandable
   - raw warning codes remain available in drilldowns/exports
7. Review key outputs:
   - June 15 decision board
   - Startup Slot / Internal Slot
   - Rookie Pick Decision Lab
   - Cut Cost / roster opportunity cost
   - Player Rank Explainer
   - Evidence Risk
   - Model Edges
   - Rookie draft board
8. Confirm review-only and no-market-leakage constraints still hold.
9. Identify any remaining blocker, high-priority, medium, or low-priority issues.

## Specific Questions

- Did the v4.5 fixes resolve the prior audit cautions?
- Is guard/admission validation now safe?
- Is the app workflow understandable for human final decision review?
- Are duplicate explainer contexts clear and traceable?
- Is 2026 5.04 safely handled without fake precision?
- Are naming and warnings human-readable enough for the user to review decisions?
- Do review-only and no-market-leakage constraints still hold?
- Is the model ready for human final decision review?

## Desired Output

Return:

- overall verdict
- critical blockers
- high-priority issues
- medium/low issues
- source/leakage concerns, if any
- UI/readability concerns, if any
- 2026 5.04 handling assessment
- final recommendation: `ready_for_human_final_decision_review`, `needs_minor_patch`, or `needs_repair_before_review`
