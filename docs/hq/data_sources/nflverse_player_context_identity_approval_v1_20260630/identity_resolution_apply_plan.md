# NFLVerse Player Context Identity Resolution Apply Plan

## Do Not Apply Yet

This packet does not contain approved identities. Every row in identity_human_decision_sheet.csv is still human_decision=PENDING and approved_by_human=false.

## Human Decision Rules

Allowed human_decision values are:

- APPROVE_REVIEW_ONLY
- KEEP_BLOCKED
- REJECT_WRONG_IDENTITY
- NEEDS_MORE_INFO
- PENDING

A future apply lane may include a row in identity_approved_overlay_v1.csv only when all are true:

- human_decision=APPROVE_REVIEW_ONLY
- approved_by_human=true
- Candidate identity is tied to the correct NWR player key without ambiguity.
- The row remains review_only=true.
- model_use_allowed=false, training_allowed=false, and source_truth_allowed=false.

## Future Apply Steps

1. Collect explicit human decisions in the decision sheet.
2. Validate every decision value against the allowed enum.
3. Reject any row where approved_by_human=true but human_decision is not APPROVE_REVIEW_ONLY.
4. Reject any row where approval depends on name-only or fuzzy evidence.
5. Create a compact approved overlay only for explicitly approved rows.
6. Rebuild the player context artifact in a separate lane only after overlay validation passes.
7. Keep all approved identity output display-only and review-only.

## Non-Goals

- No model input approval.
- No training approval.
- No source-truth approval.
- No Rankings wiring.
- No Outcome probability changes.
- No rank, tier, frozen-board, latest pointer, trade value, or pick value changes.
