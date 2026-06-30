# Identity Apply Overlay Readiness

Current readiness: NOT READY

## Why Not Ready

- Explicit approved rows: 0
- Pending rows: 54
- No approved identity overlay exists.
- Recommended review-only approvals are recommendations only.

## Future Overlay Eligibility Rules

A future overlay lane may include a row only when all are true:

- `human_decision=APPROVE_REVIEW_ONLY`
- `approved_by_human=true`
- the approval evidence is explicit and human-provided
- `review_only=true`
- `model_use_allowed=false`
- `training_allowed=false`
- `source_truth_allowed=false`
- `rank_logic_allowed=false`
- `hidden_sort_allowed=false`
- `trade_value_allowed=false`
- `pick_value_allowed=false`

## Required Future Checks

- Reject name-only or fuzzy approvals.
- Reject rows with pending, keep-blocked, rejected, or needs-more-info decisions.
- Reject approvals with missing explicit human evidence.
- Do not rebuild the player context artifact until overlay validation passes in a separate lane.
