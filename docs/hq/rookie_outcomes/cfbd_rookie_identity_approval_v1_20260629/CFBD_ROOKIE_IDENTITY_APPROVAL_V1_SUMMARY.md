# CFBD Rookie Identity Approval V1 Summary - 2026-06-29

## Verdict

`GREEN_REVIEW_ONLY_IDENTITY_APPROVAL`

The user approved CFBD identity review-only advancement for high-confidence
exact matches only. This is not model, training, or source-truth approval.

## Counts

- Input rows: 213
- Approved review-only identity rows: 157
- Deferred rows: 56
- `model_use_allowed=true` rows: 0
- `training_allowed=true` rows: 0

## Match Status Counts

- ambiguous: 10
- exact_match: 157
- possible_candidate: 46

## Identity Confidence Counts

- HIGH: 157
- LOW: 46
- MEDIUM: 10

## Guardrails

- Ambiguous and possible rows remain `approved_by_human=false`.
- All rows remain `review_only=true`.
- All rows remain `model_use_allowed=false`.
- All rows remain `training_allowed=false`.
- Approval scope is `identity_review_only`.
