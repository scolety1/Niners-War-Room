# NWR CFBD Human Review Queue

Date: 2026-06-26

Verdict: GREEN

## Source Files

Root:

`docs/hq/data_sources/cfbd_identity_matching_v1_20260624/`

Key files reviewed:

- `cfbd_identity_high_confidence_review.csv`
- `cfbd_identity_possible_review.csv`
- `cfbd_identity_ambiguous_review.csv`
- `cfbd_identity_link_registry_DRAFT.csv`
- `cfbd_identity_match_summary.csv`

## Counts

- Exact matches still needing human approval: 157
- Possible candidates: 46
- Ambiguous candidates: 10
- Draft registry rows: 213
- Draft registry rows approved by human: 0
- Rows allowed for model use: 0
- Rows allowed for training: 0
- Unmatched review-required rows: 31,614

## Morning Queue

Created:

`docs/hq/review_queue/morning_review_20260626/cfbd_identity_review_queue_v1.csv`

Queue contents:

- P0 ambiguous rows: 3 human-review items
- P1 same-name / position-conflict risk rows: 9 human-review items
- P2 exact-match approval samples and registry batch: 6 items
- Total queue rows: 18

This is intentionally concise. It does not dump all 31,614 unmatched rows or all 157 exact matches into the morning brief.

## Safe Defaults

- `model_use_allowed=false`
- `training_allowed=false`
- `approved_by_human=false`
- Do not bulk approve exact matches.
- Reject or leave unapproved same-name rows where position/team context conflicts.
- Keep CFBD review-only until a separate human approval gate.

## Human Review Priorities

1. Review ambiguous rows first: Josh Cameron, Chip Trayanum, J'Mari Taylor.
2. Reject or confirm same-name false-positive risks such as DeVonta Smith CB vs WR, Justin Jefferson LB vs WR, Caleb Williams S vs QB.
3. Spot-check exact-match rows before any approval batch.
4. Do not approve model/training use from this queue.

## Phase 4 Result

Phase 4 is GREEN. The CFBD queue prepares human review without changing approvals, source truth, model input, or training flags.
