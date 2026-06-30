# NFLVerse Approved Identity Overlay Apply Plan

## Current Status

The approved overlay exists as review-only identity evidence. It must not be consumed directly by app pages yet.

## Required Future Apply Lane

A separate Data Hygiene apply/rebuild lane must:

1. Load `identity_approved_overlay_v1.csv`.
2. Bind each approved row to the correct current NWR player row.
3. Reject any row that cannot be bound without ambiguity.
4. Preserve `review_only=true` and `display_only=true`.
5. Preserve all model/training/source-truth/rank/hidden-sort/trade/pick flags as `false`.
6. Rebuild the player context artifact only after join-key validation passes.
7. Keep non-approved rows gated as `Not enough information` / `NEED_IDENTITY_REVIEW`.

## Forbidden

- Do not use name-only or fuzzy joins.
- Do not include `RECOMMEND_HUMAN_REVIEW` or `RECOMMEND_KEEP_BLOCKED` rows.
- Do not expose rows with missing required candidate NFLVerse/GSIS IDs.
- Do not change app behavior in this lane.
- Do not promote identity overlay rows to model, rank, source truth, hidden sort, trade, or pick logic.
