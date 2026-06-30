# NFLVerse Approved Identity Overlay Summary

Verdict: GREEN_REVIEW_ONLY_IDENTITY_OVERLAY_READY

## Base

- Base branch: origin/work/hq-parallel-control
- Base HEAD at branch creation: ccfb395502c7750852b1c54ce674183b092b5937

## Human Decision Applied

The user explicitly approved rows with `recommendation=RECOMMEND_APPROVE_REVIEW_ONLY` for review-only/display-only identity use.

Rows were excluded if the recommendation was `RECOMMEND_HUMAN_REVIEW`, `RECOMMEND_KEEP_BLOCKED`, the required candidate NFLVerse/GSIS IDs were missing, or team was `needs_data` without enough supporting evidence.

## Counts

- Total decision rows: 54
- Approved overlay rows: 43
- Non-approved rows: 11
- `RECOMMEND_APPROVE_REVIEW_ONLY`: 43
- `RECOMMEND_HUMAN_REVIEW`: 4
- `RECOMMEND_KEEP_BLOCKED`: 7
- `human_decision=APPROVE_REVIEW_ONLY`: 43
- `human_decision=PENDING`: 4
- `human_decision=KEEP_BLOCKED`: 7
- Overlay rows needing NWR player ID binding before app join: 43

## Important Limitation

The approved overlay is review-only identity evidence. Because the current review rows do not carry stable `nwr_player_id` values, app lanes must not join the overlay directly into app pages until a separate Data Hygiene apply/rebuild lane safely binds approved identities to current NWR player rows.

## Non-Use Statement

This lane does not approve model input, training use, source truth, rank logic, hidden sort, trade value, pick value, recommendations, or app behavior changes.
