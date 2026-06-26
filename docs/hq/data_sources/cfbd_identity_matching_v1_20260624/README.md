# CFBD Identity Matching V1 - 2026-06-24

Run ID: `cfbd_identity_matching_v1_20260624_20260626T083313Z`
Input CFBD identity rows: 31822
Candidate output rows: 31827

## Final Review Files

- `cfbd_identity_high_confidence_review.csv`: 157 rows
- `cfbd_identity_possible_review.csv`: 56 rows
- `cfbd_identity_unmatched_priority_review.csv`: 31614 rows
- `cfbd_identity_link_registry_DRAFT.csv`: 213 rows
- `cfbd_identity_production_context_review.csv`: 5817 rows
- `cfbd_identity_review_dashboard_summary.csv`
- `cfbd_identity_final_review_method.md`

This folder contains review-only identity matching suggestions.

- Not source truth.
- Not model input.
- Not training truth.
- Human review is required before any future use.
- `model_use_allowed=false`.
- `training_allowed=false`.
- `review_required=true`.

Suggested review workflow: review high-confidence rows first, then ambiguous/possible rows, then
the unmatched priority queue. The draft registry must not be treated as approved identity truth.

The CFBD identity lane is separate from nflverse and the active NFL usage/data-loader lane.
No CFBD rows are promoted into rankings, model features, candidates, or source-truth files.
