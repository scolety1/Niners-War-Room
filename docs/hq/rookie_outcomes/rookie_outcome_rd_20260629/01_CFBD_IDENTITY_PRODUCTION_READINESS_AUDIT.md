# CFBD Identity And Production Readiness Audit - 2026-06-29

## Verdict

CFBD is not ready for rookie outcome modeling.

Primary blocker: `BLOCKED_NEEDS_CFBD_APPROVAL`

Secondary blockers: identity confidence, production-context validation, draft-link approval, and source-policy gate.

## Files Audited

- `docs/hq/data_sources/cfbd_review_artifacts_20260624/cfbd_player_identity_review_queue.csv`
- `docs/hq/data_sources/cfbd_review_artifacts_20260624/cfbd_player_production_review.csv`
- `docs/hq/data_sources/cfbd_identity_matching_v1_20260624/cfbd_identity_high_confidence_review.csv`
- `docs/hq/data_sources/cfbd_identity_matching_v1_20260624/cfbd_identity_possible_review.csv`
- `docs/hq/data_sources/cfbd_identity_matching_v1_20260624/cfbd_identity_ambiguous_review.csv`
- `docs/hq/data_sources/cfbd_identity_matching_v1_20260624/cfbd_identity_unmatched_priority_review.csv`
- `docs/hq/data_sources/cfbd_identity_matching_v1_20260624/cfbd_identity_link_registry_DRAFT.csv`
- `docs/hq/data_sources/cfbd_identity_matching_v1_20260624/cfbd_identity_production_context_review.csv`
- `docs/hq/review_queue/morning_review_20260626/cfbd_identity_review_queue_v1.csv`
- `docs/hq/review_queue/full_refresh_stats_completion_20260626/cfbd_ambiguous_identity_decisions.csv`

## Machine-Readable Output

Created:

`docs/hq/rookie_outcomes/rookie_outcome_rd_20260629/rookie_cfbd_readiness_matrix.csv`

Rows: 213 draft-registry identity candidates.

All rows keep:

- `review_only=true`
- `approved_by_human=false`
- `model_use_allowed=false`
- `training_allowed=false`

## Readiness Matrix Summary

| Status | Count | Meaning |
|---|---:|---|
| `BLOCKED_NEEDS_HUMAN_APPROVAL` | 157 | Exact review candidate, but not human-approved. |
| `BLOCKED_NEEDS_IDENTITY_CONFIDENCE` | 46 | Possible candidate requiring identity review. |
| `BLOCKED_AMBIGUOUS_IDENTITY` | 10 | Ambiguous same-name or multi-candidate group. |

Production-context status in the matrix:

| Status | Count | Meaning |
|---|---:|---|
| `REVIEW_REQUIRED_AVAILABLE` | 180 | Production context appears available, but identity and production ownership are not approved. |
| `NOT_AVAILABLE_OR_NOT_LINKED` | 33 | No linked production context was found in the review artifact. |

## High-Confidence Rows

High-confidence CFBD rows are not approvals.

Observed count: 157 exact-match review rows.

The CFBD method docs explicitly say high confidence means normalized name and position align, not that transfer history, timeline, NFL entry, or source-truth promotion are verified.

## Ambiguous And Possible Rows

Possible/ambiguous rows remain blocked.

Observed count: 56 rows:

- 46 possible candidates
- 10 ambiguous rows in the final review file

These rows cannot support rookie outcomes until a human review lane approves or rejects them.

## Unmatched Priority Queue

Observed unmatched priority rows: 31,614.

These are broad college roster rows. Most should remain unmatched unless they become fantasy-relevant and receive identity evidence.

## Draft Link Registry

Observed draft link registry rows: 213.

Registry status: `DRAFT_REVIEW_ONLY`.

All rows keep `approved_by_human=false`, `model_use_allowed=false`, and `training_allowed=false`.

## Production Context Validity

CFBD production context exists, but it is not yet validated as belonging to the matched NWR/Sleeper player.

Key risks:

- wrong school/team due to transfer timeline
- same-name collisions
- wrong position
- duplicated or stale roster rows
- production stats attached to the wrong CFBD identity
- 2026 roster/stats zero-row limitation

Production alone must not approve identity.

## Review Queue Parse Warning

`docs/hq/review_queue/full_refresh_stats_completion_20260626/cfbd_ambiguous_identity_decisions.csv` did not parse cleanly with the default CSV parser during this audit.

This warning is preserved as a blocker. The file should not be used as machine-readable approval truth until repaired.

## Safe Conclusion

Current CFBD artifacts are useful for human review and future readiness planning only.

They are not approved for:

- rookie outcome labels
- rookie outcome probabilities
- model input
- training truth
- source truth
- Rankings display columns
