# Current Board Deterministic Rebuild With Recovery Inputs V1 Report

## Verdict

`GREEN_CURRENT_BOARD_DETERMINISTIC_REBUILD_EXACT_MATCH`

## Clear Answer

The current app-visible candidate board can now be rebuilt deterministically into a review artifact path because the recovered inputs contain the pre-candidate board, current-value checkpoint/component rows, and lifecycle age receipts needed by the existing WR/QB v2 candidate row logic. The rebuilt board SHA256 matches the pinned final board hash exactly.

## Rebuild Result

| Check | Result | Match? | Evidence | Caveat |
| ----- | ------ | ------ | -------- | ------ |
| row count | rebuilt=240; pinned final=240 | true | `CURRENT_BOARD_RECOVERY_REBUILD_COMPARISON.csv` |  |
| player IDs | ordered player IDs match | true | `CURRENT_BOARD_RECOVERY_REBUILD_COMPARISON.csv` |  |
| ranks | `nwr_rank` values match | true | `CURRENT_BOARD_RECOVERY_REBUILD_COMPARISON.csv` |  |
| `checkpoint_review_score` | matches=232; mismatches=0 | true | `current_player_value_full_board_review_rows.csv` | Compared to rebuilt `base_nwr_dynasty_score`. |
| `nwr_dynasty_score` | field diff count=0 | true | `CURRENT_BOARD_RECOVERY_REBUILD_FIELD_DIFFS.csv` |  |
| final board hash | rebuilt=263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4; pinned=263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4 | true | `CURRENT_BOARD_RECOVERY_REBUILD_HASH_AUDIT.csv` |  |

## Input Mapping

See `CURRENT_BOARD_RECOVERY_REBUILD_INPUT_MAP.csv`.

The exact original `veteran_player_inputs.csv` age sidecar remains absent. This lane used a review-safe QB age adapter derived from recovered lifecycle receipt rows (`age_years_decimal`) and wrote it to `review_safe_qb_age_adapter_from_lifecycle_receipts.csv`. This adapter reproduced the pinned board exactly and is not a production source promotion.

## Hash Audit

Rebuilt board hash:

`263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4`

Pinned final board hash:

`263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4`

The rebuilt hash matches the pinned final board hash exactly.

## Field Diff Summary

Total detailed field diffs: `0`.

See `CURRENT_BOARD_RECOVERY_REBUILD_FIELD_DIFFS.csv` and `CURRENT_BOARD_RECOVERY_REBUILD_DETAILED_FIELD_DIFFS.csv`.

## Receipt Chain

See `CURRENT_BOARD_RECOVERY_REBUILD_RECEIPT_CHAIN.csv`.

Current-board `checkpoint_review_score` is reconciled to rebuilt `base_nwr_dynasty_score` for `232` rows with `0` mismatches.

Current-board `nwr_dynasty_score` is reconciled exactly to the rebuilt final candidate board.

## Shadow Metrics Status

`shadow_model_v2_metrics.csv` remains missing. It is not required for the exact board-row hash rebuild performed here, but it remains a blocker for exact shadow/guardrail historical replay if a future lane requires those historical metrics.

## Production Status

- Current board remains `candidate_review_only_main_display`.
- Row-level stamp remains `candidate_review_only_not_active_rankings`.
- Candidate mode remains `wr_qb_v2_candidate`.
- No active production formula is approved by this lane.
- No source was promoted.
- No ranking output was changed.
- No app behavior was changed.
- Exact historical replay remains blocked until season-by-season receipts and missing sidecars are separately backfilled and approved.

## Recommendation

Recommended next lane: `Model v4 production-active human review packet`.

This should be a human review packet, not an automatic promotion. It should decide whether the now-rebuilt current board is eligible for any production-active review discussion while preserving the candidate/review-only status until separately approved.
