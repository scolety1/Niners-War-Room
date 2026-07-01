# Label Truth Guardrail Report

Verdict: `NO_LABEL_TRUTH_PROMOTION`

## Approval Invariants

The coverage matrix keeps all activation approvals false:

- `label_truth_allowed=false`
- `model_use_allowed=false`
- `training_allowed=false`
- `source_truth_allowed=false`

Because no row-level sidecar rows were created, `sidecar_review_allowed=false` for every coverage row in this packet.

## Label Policy

Existing Outcome labels remain evaluation targets only. They are not input features. NFLVerse player_stats is not label truth unless a later explicit parity gate approves it.

## Missingness Policy

- Missing row-level player_stats source data is `Not enough information`.
- Missing stats are not zero production.
- Missing sidecar rows are not failed outcomes.
- Incomplete windows are censored, not misses.

## Runtime Guardrails

This packet does not alter app behavior, Rankings, Player Compare, Rookie Outcomes, model logic, source truth, rank logic, hidden sort, trade value, pick value, or probabilities.
