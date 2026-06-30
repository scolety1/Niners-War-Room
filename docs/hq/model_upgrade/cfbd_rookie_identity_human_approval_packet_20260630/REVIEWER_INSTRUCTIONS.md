# Reviewer Instructions

Use `candidate_identity_review_v1.csv` as the read-only inspection table and `approval_template_v1.csv` as the fill-in worksheet.

## Review Order

1. Start with `KEEP_BLOCKED` and `REJECT_WRONG_PLAYER` rows in `blocked_needs_more_info_v1.csv`.
2. Resolve duplicate or ambiguous groups before approving any related row.
3. Spot-check `APPROVE_REVIEW_ONLY` rows in batches. Do not bulk approve exact-name rows without checking position, school/team, and timeline.
4. Leave uncertain rows as `NEEDS_MORE_INFO` or `KEEP_BLOCKED`.

## Approval Rules

Approve review-only only when all of these fit:

- Player name.
- Position.
- School/team context.
- Timeline or season context.
- Candidate NWR/Sleeper identifier if available.
- CFBD identifier if available.

Do not approve when there is:

- Same-name conflict.
- Transfer confusion that changes the timeline.
- Wrong position.
- Wrong school/team.
- Wrong year or impossible timeline.
- Missing identifier needed for a safe join.

## How To Fill The Template

Set `human_decision` to exactly one of:

- `APPROVE_REVIEW_ONLY`
- `KEEP_BLOCKED`
- `NEEDS_MORE_INFO`
- `REJECT_WRONG_PLAYER`

Keep the default flags unchanged:

- `approved_by_human=false` until the reviewer intentionally changes it in a future accepted artifact.
- `model_use_allowed=false`.
- `training_allowed=false`.
- `review_only=true`.

This V1 packet itself does not change any approval flags.
