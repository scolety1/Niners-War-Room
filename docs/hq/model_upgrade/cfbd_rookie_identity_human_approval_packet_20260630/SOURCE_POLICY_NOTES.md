# Source Policy Notes

This packet is a human-review source gate only.

## Allowed Now

- Inspect candidate CFBD identity links.
- Mark a future human decision in `approval_template_v1.csv`.
- Approve an identity link for review-only use after confirming name, position, school/team, and timeline.
- Keep blocked or reject same-name conflicts, wrong-position rows, wrong-team rows, transfer confusion, wrong-year rows, and missing-identifier rows.

## Not Allowed

- CFBD model input.
- CFBD training use.
- CFBD production/context as Dynasty Rank evidence.
- Rookie probabilities.
- Player values.
- Model features except review-only candidates in later gates.
- Ranking, tier, final-board, hidden-sort, draft-room, or runtime changes.
- `latest_candidate` or `latest_approved` mutation.

## Decision Semantics

`APPROVE_REVIEW_ONLY` is an identity-review status only. It does not open model, training, rank, source-truth, or app gates.

`KEEP_BLOCKED` should be used when the row is ambiguous, conflicted, or unsafe but should remain visible for future review.

`NEEDS_MORE_INFO` should be used when a specific missing source or field is required before a decision.

`REJECT_WRONG_PLAYER` should be used when the candidate appears to be a different player, such as same name but wrong position or impossible timeline.

Missing data must remain `Not enough information`. It must never become zero, false, bad, healthy, low probability, or a rank penalty.
