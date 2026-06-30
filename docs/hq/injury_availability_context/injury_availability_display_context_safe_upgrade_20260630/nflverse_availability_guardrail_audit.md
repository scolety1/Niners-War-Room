# NFLVerse Availability Guardrail Audit

Verdict: `PASS`

## Identity Gate

Detailed NFLVerse context displays only when:

- `identity_join_status=SAFE_NOW_DISPLAY_ONLY`
- `review_required=false`
- the displayed field has `field_status=SAFE_NOW_DISPLAY_ONLY` in the schema manifest

Rows with `NEED_IDENTITY_REVIEW` show only `Review needed`; detailed roster, injury,
practice, snap, last-active, and age context remains `Not enough information`.

## Missing Data Rules

- Missing injury report status is not healthy.
- Missing roster status is not clean, safe, active, or inactive.
- Missing weekly roster status is not clean, safe, active, or inactive.
- Missing snap data is not zero.
- Missing schedule context is not a bye or no game.
- Missing values display as `Not enough information`.

## Blocked Uses

This lane does not add:

- injury-risk score
- medical projection
- ACL/comeback projection
- durability score
- hidden sort
- model input
- rank logic
- source-truth promotion
- recommendation logic
- trade value
- pick value

## Source Rules

Player Compare and Rankings consume the tracked repo player context artifact. They
do not read raw `C:\NWR_SHARED_DATA` NFLVerse files for this display.

`ff_rankings` remains blocked and unused.

## Protected Outputs

No model, rank, tier, source-truth, Outcome probability, latest approved, pinned
snapshot, trade value, pick value, or recommendation artifact is changed.
