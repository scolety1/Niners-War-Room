# Model v4 Status Taxonomy Proposal

## Purpose

This taxonomy separates current-board reproducibility, app visibility, candidate status, review safety, production approval, source approval, and historical accuracy. The goal is to stop one status string from carrying too many meanings.

## Canonical Machine-Friendly Values

### Board-Level Status

Recommended value:

`candidate_review_only_main_display_rebuild_verified`

Meaning:

- Current app-visible board.
- Candidate/review-only board.
- Exact current hash rebuild verified.
- Main display surface for human review.
- Not production-active.
- Not historically accuracy-approved.

### Row-Level Allowed Use

Recommended value:

`candidate_review_only_rebuild_verified_not_production_active`

Meaning:

- Row belongs to the rebuild-verified current candidate board.
- Row is review-only.
- Row may support human draft review.
- Row may not be used as a production-active ranking or autonomous recommendation.

### Candidate Mode

Recommended value:

`wr_qb_v2_candidate`

Meaning:

- Preserve the exact candidate overlay identifier.
- Do not use this field as a production approval flag.

### Rebuild Verification Status

Recommended value:

`hash_rebuild_verified_exact_match`

Meaning:

- Rebuilt board hash equals pinned final board hash.
- Field diffs are zero.
- `checkpoint_review_score` and `nwr_dynasty_score` reconcile for the current board.

### Production Approval Status

Recommended value:

`not_production_active_pending_human_approval`

Meaning:

- No production-active approval exists.
- Human approval and separate gates are required before production use.

### Historical Replay Status

Recommended value:

`exact_historical_replay_blocked`

Meaning:

- Current exact rebuild does not create season-by-season historical receipts.
- No historical accuracy claim should be made from current rebuild evidence alone.

### Accuracy Approval Status

Recommended value:

`not_historically_accuracy_approved`

Meaning:

- Prior proxy backtest had useful signal but did not beat the simple prior-year finish baseline overall.
- Exact formula historical replay benchmark is not available yet.

### Source Promotion Status

Recommended value:

`not_source_promoted`

Meaning:

- No source-truth, model-use, training-use, UI-use, or production-use promotion follows from label correction.

## Human-Facing Terms

Preferred short badge:

`Review-only, rebuild verified`

Preferred board name:

`Model v4 Review Board`

Preferred caution:

`Not production-active or historically accuracy-approved`

## Terms To Avoid

- `approved rankings`
- `approved NWR score`
- `active rankings`
- `production rankings`
- `final model`
- `accuracy-approved`
- `source-truth`
- `draft recommendation`
- `trade value`

These terms imply a level of approval not supported by current evidence.
