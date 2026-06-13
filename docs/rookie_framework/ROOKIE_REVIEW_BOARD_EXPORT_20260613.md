# Rookie Review Board Export - 2026-06-13

## Purpose

The Rookie Review Board v0.3 export converts local v0.3 candidate artifacts into human-reviewable CSV and Markdown outputs. It is designed to make rookie evidence easier to inspect without creating final rankings, probabilities, bands, production scoring, app-readable outcome columns, or veteran outcome-head inputs.

## Inputs

The export reads local rookie framework artifacts from `local_exports/model_v4/rookie_framework_v02/`:

- `v03_candidate_01/v03_candidate_player_review_board.csv`
- `v03_candidate_01/v03_candidate_premium_pick_board.csv`
- `v03_candidate_01/v03_candidate_round2_board.csv`
- `v03_candidate_01/v03_candidate_5_04_board.csv`
- `deep_research_intake_pass_04/deep_research_manual_review_flags.csv`
- `deep_research_intake_pass_04/deep_research_remaining_gaps_after_pass04.csv`
- `deep_research_intake_pass_04/deep_research_source_safety_audit.csv`
- `deep_research_intake_pass_04/deep_research_conflict_review.csv`
- `v03_adversarial_audit_01/v03_adversarial_findings.csv`
- `v03_adversarial_audit_01/v03_patch_queue.csv`
- `OVERNIGHT_QUEUE_FINAL_SUMMARY_20260612.md`

If required inputs are missing, the exporter stops and reports the missing files. It does not fabricate data.

## Outputs

The exporter writes local-only outputs under `local_exports/model_v4/rookie_framework_v02/review_board_v03/`:

- `rookie_review_board_v03.csv`
- `rookie_review_board_premium_review_v03.csv`
- `rookie_review_board_round2_v03.csv`
- `rookie_review_board_5_04_watchlist_v03.csv`
- `rookie_review_board_manual_flags_v03.csv`
- `rookie_review_board_remaining_gaps_v03.csv`
- `README_ROOKIE_REVIEW_BOARD_V03.md`

Generated local exports are not tracked and must not be committed.

## Required Columns

The main review-board outputs include:

- `player_id`
- `player_name`
- `position`
- `school`
- `current_pick_zone`
- `v03_candidate_pick_zone`
- `review_bucket`
- `position_group`
- `tag_summary`
- `hard_caps`
- `soft_flags`
- `manual_review_flags`
- `urgent_manual_questions`
- `source_confidence`
- `best_source_safe_evidence_summary`
- `remaining_true_gaps`
- `prohibited_sources_detected`
- `source_conflict_status`
- `review_status`
- `notes`

Output column names intentionally avoid final ordering, value, probability, and band semantics.

## Review-Status Definitions

- `review_needed`: player or field remains eligible for human review.
- `needs_data`: player has source-safe gaps and no urgent manual flag in the candidate row.
- `capped_review`: player remains blocked by hard caps or cap action.
- `watchlist_review`: 5.04 watchlist context only.
- `hold_until_roster_declaration`: legal-pool or manual-add context should wait for roster declaration.
- `unavailable`: insufficient source-safe artifact context.

## Source-Safety Rules

- Preserve `use_now`, `use_as_soft_flag`, `manual_review_only`, `unavailable`, `excluded`, and `conflict_review` distinctions.
- Keep soft flags soft; do not convert them to hard private value.
- Keep manual-review-only notes manual-review-only.
- Preserve hard caps, soft flags, manual-review flags, source conflicts, and remaining gaps.
- Flag prohibited source context from the source-safety audit without promoting it.
- Strict mode fails if prohibited input columns or market contamination blockers are detected.
- Do not import app or Streamlit modules.
- Do not mutate source files.

## How This Differs From Rankings

The review board is not sorted by player value, model output, market signal, projection, consensus, ADP, or draft recommendation. Sorting is deterministic only: review bucket, position, player name, and player id.

The board does not choose players. It shows what still needs review and which source-safety constraints apply.

## Why This Is Safe Before Final Rookie Ranking Work

This export stays in the review layer. It uses existing v0.3 candidate artifacts, preserves caveats, surfaces manual questions, and writes only local-only outputs. It does not change active rankings, private scores, formulas, app files, outcome files, veteran outcome heads, `data/`, or promoted model artifacts.

## Support For Later Shadow Work

The review board can support a later shadow rookie ordering experiment only after review-board outputs are green. Any future shadow work must remain non-production, non-app, and separately gated, with no probabilities, bands, production promotion, or veteran outcome-head usage.
