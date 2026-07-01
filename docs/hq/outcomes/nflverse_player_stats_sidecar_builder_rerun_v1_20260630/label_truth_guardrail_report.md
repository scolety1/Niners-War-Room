# Label Truth Guardrail Report

Verdict: `NO_LABEL_TRUTH_PROMOTION`

## Approval Invariants

The rerun coverage matrix keeps all activation approvals false:

- `label_truth_allowed=false`
- `model_use_allowed=false`
- `training_allowed=false`
- `source_truth_allowed=false`

Because no compact sidecar rows were created, `sidecar_review_allowed=false` for every coverage row in this packet.

## Label Policy

Existing Outcome labels remain evaluation targets only. They are not input features. NFLVerse player_stats is not label truth unless a later explicit parity gate approves it.

## Source Policy

The source admission receipt permits future review-only sidecar builder use for the two admitted receipt rows. It does not approve player_stats as label truth, model input, training input, source truth, rank logic, hidden sort, recommendations, trade value, or pick value.

## Missingness Policy

- Missing compact sidecar derivation is `Not enough information`.
- Missing stats are not zero production.
- Missing sidecar rows are not failed outcomes.
- Incomplete windows are censored, not misses.

## Runtime Guardrails

This packet does not alter app behavior, Rankings, Player Compare, Rookie Outcomes, model logic, source truth, rank logic, hidden sort, trade value, pick value, or probabilities.
