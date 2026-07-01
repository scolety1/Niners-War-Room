# Label Truth Guardrail Report

Verdict: `NO_LABEL_TRUTH_PROMOTION`

## Required Posture

The sidecar matrix preserves these invariants for every row:

- `label_truth_allowed=false`
- `model_use_allowed_now=false`
- `training_allowed_now=false`
- `source_truth_allowed_now=false`

`sidecar_review_allowed=true` means only that NFLVerse player_stats may be compared later in a review-only evidence lane.

## Existing Labels

Existing Outcome labels remain evaluation targets. They are not input features and are not replaced by NFLVerse player_stats.

## NFLVerse Player Stats

NFLVerse player_stats is not label truth unless a later explicit parity gate approves it. This packet does not approve such a gate.

## Rookie Outcomes

No active rookie probabilities are approved. Rookie Gate G remains blocked. Drafted-only review evidence remains review-only.

## Missingness and Censoring

- Missing labels are not failures.
- Missing player_stats rows are not failures.
- Incomplete labels are censored.
- Censored windows are not misses.
- Missing data is `Not enough information`, not `0%`, false, healthy, clean, or low risk.

## App and Model Guardrails

This packet does not alter Rankings, Player Compare, Rookie Outcomes, model behavior, hidden sort, Dynasty Rank, tiers, source truth, trade value, or pick value.
