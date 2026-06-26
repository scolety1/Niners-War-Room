# CFBD Identity Matching V1 Final Review Method

## How To Use This Package

Start with `cfbd_identity_review_dashboard_summary.csv`, then review the focused CSVs in this order:

1. `cfbd_identity_high_confidence_review.csv`
2. `cfbd_identity_possible_review.csv`
3. `cfbd_identity_unmatched_priority_review.csv`
4. `cfbd_identity_link_registry_DRAFT.csv`

The draft registry is a work queue, not source truth. Human reviewers should fill the blank
`human_decision`, `human_reviewer`, `human_review_date`, and `review_note` fields in a future
review lane or copied review sheet. This package itself does not approve any link.

## Why HIGH Is Not Automatically Approved

`HIGH` means the normalized CFBD name and position align with one existing NWR/Sleeper reference.
It does not verify transfer history, draft class timing, NFL landing spot, duplicate identities, or
whether the existing source should be treated as authoritative for CFBD. Every row remains
`review_required=true`.

## What Humans Should Approve Or Reject Later

- Approve only when the CFBD player and candidate identity are clearly the same person.
- Reject when names are aliases/collisions or college/NFL context conflicts.
- Defer when more identity evidence is needed.
- Never use production stats alone to approve identity.

## Why Unmatched Rows Are Expected

The CFBD roster covers broad college football rosters, while NWR/Sleeper/final-board sources cover a
smaller fantasy/draft-relevant universe. Most CFBD rows should remain unmatched in V1.

## Why This Is Not Model Input

All outputs keep `model_use_allowed=false`, `training_allowed=false`, and `review_required=true`.
No candidate rank, Dynasty Rank, final board rank, tiers, source truth, or model feature files are
created or changed.

## Counts

- Source CFBD rows: 31822
- High-confidence review rows: 157
- Possible/ambiguous review rows: 56
- Unmatched priority rows: 31614

## CFBD Identity Matching V2 Next Steps

- Add a human-review workflow for approve/reject/defer decisions.
- Add row-level recruiting context only if a tracked review-only recruiting artifact exists.
- Add transfer/team-season context before any source-truth promotion.
- Design a separate promotion gate after manual review and backtesting requirements are defined.
