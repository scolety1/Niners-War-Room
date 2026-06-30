# Statistic Analysis Design

Status: DEFER for exact contribution percentages.

Future candidate status: MODEL_FEATURE_CANDIDATE.

`Statistic Analysis` is a read-only score explanation view. It helps answer why a player has the displayed NWR Score using only currently approved metadata columns from the full dynasty rankings artifact.

The current approved rankings artifact exposes:

- `nwr_dynasty_score`
- `score_status`
- `score_type`
- `score_as_of_date`
- `base_nwr_dynasty_score`
- `confidence_cap`
- `confidence_status`
- `allowed_use`
- `blocked_use`
- `candidate_evidence_fields_used`
- `trust_status`
- `manual_review_flag`
- `candidate_key_caveat`

The current artifact does not expose approved component-level score rows, component weights, weighted contribution amounts, or percent contribution columns. Therefore this lane does not calculate or display invented score breakdown math.

Main-table unsupported fields such as `Contribution %`, `Missing Component Count`, and `Capped Component Count` display `Not enough information`.

To safely compute true contribution percentages later, the scoring pipeline would need an approved component receipt artifact keyed to the exact displayed score row. That artifact would need component names, component scores, weights, caps, weighted contribution values, reconciliation to the displayed NWR Score, source/gate metadata, and missing-value semantics.

Guardrail language:

- Statistic Analysis: Read-only score explanation view. Does not change Dynasty Rank, tiers, or model/source approvals.
- Component columns: Current displayed score component if available. Missing means not enough information, not zero or bad.
- Contribution percentage: Shown only when safely decomposable from current scoring artifacts. Does not imply independent player value.
- Market fields: External market context only. Not rank logic, not model input, not trade value, and not a replacement for Dynasty Rank.
- Outcome fields: Display-only/review-only outcome context. Missing data means not enough information, not low probability.
- Injury/availability fields: Review-only availability context. Not a medical projection and not a current-health judgment.
