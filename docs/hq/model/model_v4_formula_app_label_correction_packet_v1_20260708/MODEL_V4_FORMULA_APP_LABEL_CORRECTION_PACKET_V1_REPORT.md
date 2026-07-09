# Model v4 Formula / App-Label Correction Packet V1 Report

Date: 2026-07-08

Branch: `work/lane-model-v4-formula-app-label-correction-packet-v1-20260708`

Base HQ HEAD verified: `e1c2359f492b03e35d0ba1853ffebaf8a011b232`

## Verdict

`GREEN_MODEL_V4_LABEL_CORRECTION_PACKET_READY`

## Clear Answer

The current board label should be corrected because the board is app-visible and exact hash-rebuild verified, but its row-level status still reads `candidate_review_only_not_active_rankings`. That wording correctly blocks production use, but it is now too ambiguous: it can sound inactive or stale even though the board is the current main display and reproducible. The corrected terminology should say the board is review-only, app-visible, hash-rebuild verified, usable only as a human draft aid, not production-active, and not historically accuracy-approved.

This lane does not implement the correction. It proposes the terminology and guardrails for a later implementation lane.

## Current Label Problem

The current label stack mixes four truths that need to be separated:

1. The board is app-visible as the main Full Dynasty display.
2. The board is a candidate/review-only Model v4 WR/QB v2 board.
3. The board is now exactly rebuild verified from recovered inputs.
4. The board is not production-active and not historically accuracy-approved.

The current row-level `allowed_use` value, `candidate_review_only_not_active_rankings`, protects against production use but does not communicate that the board is the current main display or that the hash-rebuild evidence has passed. Older app/docs wording also uses "approved" around the current rankings artifact and score metadata, which now needs narrower wording.

## Proposed Canonical Status

Recommended board-level status:

`candidate_review_only_main_display_rebuild_verified`

Recommended row-level status / `allowed_use` replacement:

`candidate_review_only_rebuild_verified_not_production_active`

Recommended human-facing status badge:

`Review-only, rebuild verified`

Recommended production approval status:

`not_production_active_pending_human_approval`

Recommended historical accuracy status:

`not_historically_accuracy_approved`

These values preserve candidate/review-only status while removing the misleading implication that the board is simply inactive.

## UI Wording Recommendations

Safe board header:

`Model v4 Review Board`

Safe status line:

`Hash-rebuild verified current board. Review-only human draft aid. Not production-active or historically accuracy-approved.`

Safe tooltip/help text:

`This board exactly rebuilds to the pinned current hash and is visible as the main review board. It remains candidate/review-only: it does not approve production ranking use, source promotion, autonomous recommendations, trade logic, draft logic, or historical accuracy.`

Safe draft-day note:

`Use as a human review aid only. Prior proxy accuracy did not beat the simple prior-year finish baseline overall, so historical superiority is not proven.`

## Artifact Field Recommendations

| Field | Current Value | Recommended Value | Reason | Requires Implementation Lane? |
| ----- | ------------- | ----------------- | ------ | ----------------------------- |
| Board-level status | `candidate_review_only_main_display` | `candidate_review_only_main_display_rebuild_verified` | Adds exact rebuild proof without implying production activation. | Yes |
| Row-level `allowed_use` | `candidate_review_only_not_active_rankings` | `candidate_review_only_rebuild_verified_not_production_active` | Removes inactive/stale ambiguity while preserving production block. | Yes |
| `candidate_mode` | `wr_qb_v2_candidate` | `wr_qb_v2_candidate` | Accurate candidate-mode identifier; keep unchanged. | No |
| Formula ID | mixed current values | `model_v4_review_board_wr_qb_v2_candidate_2026_pre_draft` | Gives future docs a clear review-board formula label without claiming production. | Yes |
| Rebuild verification | implicit via report/hash | `hash_rebuild_verified_exact_match` | Makes the exact rebuild result machine-readable. | Yes |
| Production approval | absent/not active | `not_production_active_pending_human_approval` | Prevents accidental promotion. | Yes |
| Historical replay | blocked | `exact_historical_replay_blocked` | Preserves replay blocker. | Yes |
| Accuracy approval | absent | `not_historically_accuracy_approved` | Preserves cold-water backtest caveat. | Yes |

## Guardrails

The corrected label must not imply:

- Production-active approval.
- Source-truth promotion.
- Model-use source promotion.
- Historical accuracy approval.
- Superiority over prior-year finish.
- Default sort change.
- Hidden sort change.
- Recommendation, trade, draft, cut, keep, buy, sell, defer, or start/sit logic.
- Formula tuning or model weight change.
- Permission to reuse current-only fields in historical replay.

## Recommended Next Lane

Recommended next lane: `App-visible label correction implementation lane`.

The implementation lane should change only approved display/status wording and/or artifact status fields after human approval. It must include tests or scans proving no score, rank, formula weight, default sort, hidden sort, source gate, recommendation logic, trade logic, draft logic, or model output changed.

Production-active approval remains blocked. Historical accuracy remains unproven.
