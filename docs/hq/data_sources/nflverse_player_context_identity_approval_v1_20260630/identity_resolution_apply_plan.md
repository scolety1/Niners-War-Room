# NFLVerse Player Context Identity Resolution Apply Plan

## Status

The human decision sheet now records explicit review-only/display-only approval for 43 rows and keeps the remaining 11 rows pending or blocked.

A review-only approved overlay was created at:

`docs/hq/data_sources/nflverse_player_context_identity_approved_overlay_20260630/identity_approved_overlay_v1.csv`

## Overlay Eligibility Rules Used

Rows were eligible only when all were true:

- `recommendation=RECOMMEND_APPROVE_REVIEW_ONLY`
- `human_decision=APPROVE_REVIEW_ONLY`
- `approved_by_human=true`
- candidate NFLVerse ID present
- candidate GSIS ID present
- team is not `needs_data`
- `review_only=true`
- model/training/source-truth/rank/hidden-sort/trade/pick flags remain false

## Future Apply Steps

1. Load the approved overlay.
2. Bind approved identities to current NWR player rows without ambiguity.
3. Reject name-only or fuzzy joins.
4. Keep non-approved rows gated.
5. Rebuild the player context artifact only in a separate lane after join-key validation passes.
6. Keep all identity output display-only and review-only.

## Non-Goals

- No model input approval.
- No training approval.
- No source-truth approval.
- No Rankings wiring.
- No Outcome probability changes.
- No rank, tier, frozen-board, latest pointer, trade value, or pick value changes.
