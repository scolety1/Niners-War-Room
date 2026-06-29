# Gate B Draft Capital Blocker - 2026-06-29

## Gate Result

`BLOCKED_NEEDS_DRAFT_CAPITAL`

Gate A is now green for review-only identity approval, but Gate B is not
green because no tracked approved draft-capital artifact covers the
approved identity subset and historical rookie classes.

## Evidence

- Approved CFBD identity review-only rows: 157
- 2026 draft capital exists only as a documented/local-only snapshot.
- Historical draft capital remains missing or prototype/sample-only.
- UDFA status, drafted team, age at draft, and historical coverage are not
  available in a tracked approved artifact for this lane.
- No local_exports/raw/source-cache data was promoted.

## Source Audit

- CFBD rookie identity approval V1: blocked_identity_only_not_draft_capital (identity_review_only)
- CFBD identity link registry DRAFT: blocked_partial_not_approved (partial)
- 2026 draft capital snapshot doc: blocked_partial_not_approved (partial_local_only)
- Historical rookie replay templates: blocked_missing (missing)
- Historical rookie replay sample data: blocked_partial_not_approved (sample_only)
- Model v4 rookie outcome labels service: blocked_policy (blocked_policy)
- fact_rookie_draftables template: blocked_missing (missing)

## Stop Decision

The lane stops at Gate B. Gates C-G were not run, and no rookie outcome
probabilities, labels, display artifacts, or Rankings columns were created.
