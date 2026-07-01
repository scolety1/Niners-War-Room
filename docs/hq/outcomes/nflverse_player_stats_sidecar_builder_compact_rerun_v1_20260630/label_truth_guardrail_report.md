# Label Truth Guardrail Report

Verdict: `NO_LABEL_TRUTH_PROMOTION`

## Approval Invariants

The official sidecar artifact keeps all activation approvals false for every row:

- `label_truth_allowed=false`
- `model_use_allowed=false`
- `training_allowed=false`
- `source_truth_allowed=false`

`sidecar_review_allowed=true` means only review-only comparison substrate use.

## Label Policy

Existing Outcome labels remain evaluation targets only. They are not input features. NFLVerse player_stats sidecar rows are not label truth unless a later explicit parity gate approves it.

## Missingness Policy

- Missing data remains `Not enough information`.
- Absence from the compact candidate is not zero production.
- Missing stats are not false outcomes.
- Incomplete windows are censored, not misses.

## Runtime Guardrails

This packet does not alter app behavior, Rankings, Player Compare, Rookie Outcomes, model logic, source truth, rank logic, hidden sort, trade value, pick value, or probabilities.
