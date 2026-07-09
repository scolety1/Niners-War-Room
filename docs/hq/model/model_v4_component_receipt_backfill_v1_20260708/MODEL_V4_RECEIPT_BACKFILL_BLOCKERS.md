# Model v4 Receipt Backfill Blockers

Date: 2026-07-08

## Verdict

`CURRENT_BOARD_RECONSTRUCTION_BLOCKED_BY_MISSING_RUNTIME_RECEIPTS`

## Ranked Blockers

1. Missing upstream base full-board file:
   `local_exports/model_v4/current_value/latest/current_player_value_full_board_review_rows.csv`

   The current board names this as the upstream source for `checkpoint_review_score`, but it is absent from the fresh worktree and the app control runtime folder.

2. Missing current checkpoint review rows:
   `local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv`

   Without this file, `checkpoint_review_score` cannot be compared row-by-row.

3. Missing checkpoint component and receipt rows:
   `current_player_value_component_rows.csv`, `current_player_value_receipts.csv`, and `current_player_value_warnings.csv`

   These are required to reconcile `position_specific_review_score * lifecycle_modifier_review * confidence_cap`.

4. Missing RB/WR component rows and receipts:
   `rb_wr_current_value_review_rows.csv`, `rb_wr_current_value_component_rows.csv`, and `rb_wr_current_value_receipts.csv`

   Code exposes weights, but row-level raw values, normalized scores, and weighted contributions are absent.

5. Missing QB/TE component rows and receipts:
   `qb_te_current_value_review_rows.csv`, `qb_te_current_value_component_rows.csv`, and `qb_te_current_value_receipts.csv`

   Code exposes weights and discipline context, but the current row receipts are absent.

6. Missing replacement/VORP rows and receipts:
   `local_exports/model_v4/replacement_vorp/latest/player_vorp_review_rows.csv` and related component/receipt files

   This blocks `positive_vorp_points`, `review_scoring_points`, and first-down point proof.

7. Missing admitted first-down and return-scoring receipt artifacts:
   `admitted_rushing_first_downs.csv`, `admitted_receiving_first_downs.csv`, and `admitted_return_scoring_evidence.csv`

   These cannot be inferred from final board scores.

8. Missing lifecycle and confidence/missingness receipts:
   `lifecycle_archetype_*` and `confidence_missingness_*` files

   These block lifecycle modifier and confidence cap proof.

9. Missing WR/QB v2 candidate output folder:
   `local_exports/model_v4/current_value/candidates/wr_qb_v2`

   The final board has candidate reason fields, but the reason-code report, guardrail report, and candidate summary are absent.

10. Candidate policy stamp remains:
    `candidate_review_only_not_active_rankings`

    Even a successful reconstruction would not by itself promote the board to active production.

## Backfill Decision

This lane backfilled only observed final-board field receipts. It did not generate upstream component receipts because doing so would require missing input artifacts and would risk fabricating formula evidence.

## Required Next Fix

A current-board deterministic rebuild fix lane should first recover or regenerate the exact current receipt chain into a review-safe output path:

1. Replacement/VORP rows, components, receipts, warnings.
2. RB/WR and QB/TE value rows, components, receipts, warnings.
3. Lifecycle rows, components, receipts, warnings.
4. Confidence rows, receipts, warnings.
5. Current checkpoint rows, components, receipts, warnings.
6. Base full-board rows.
7. WR/QB v2 candidate overlay outputs and guardrail reports.
8. Hash comparison against the pinned final board.
