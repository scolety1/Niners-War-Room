# Model v4 Active Formula Contract

Date: 2026-07-08

Status: `REVIEW_ONLY_CONTRACT_PARTIAL_WITH_RECEIPT_BLOCKERS`

## Contract Summary

The active production formula is not identifiable from local evidence. The current app-visible Full Dynasty board is a review/candidate artifact with final displayed columns, but it is not supported by a complete source-traced receipt chain and is stamped as not active rankings.

Until a promotion receipt or label correction is produced, future lanes must use this contract:

- Current formula ID: `model_v4_wr_qb_v2_old_pocket_qb_guardrail` for scored current board rows; `model_v4_full_player_board_value_0.1.0` for unscored/fallback rows.
- Current ranking surface status: `candidate_review_only_main_display`.
- Current score column: `nwr_dynasty_score`.
- Current rank column: `nwr_rank`.
- Current row policy: `allowed_use = candidate_review_only_not_active_rankings`.
- Current candidate mode: `wr_qb_v2_candidate`.
- Production-active status: not proven.
- Historical replay status: blocked.

## Files And Functions That Generate Or Display The Board

| Layer | File/Function | Contract Role |
| --- | --- | --- |
| App display | `app/pages/20_final_board_v1.py` | Displays app presets and sort controls over the loaded rankings frame. |
| App loader | `src/services/draft_day_app_v1_service.py::load_dynasty_rankings()` | Loads hash-pinned current board artifact and validates required fields. |
| App board merge | `src/services/draft_day_app_v1_service.py::build_unified_player_board()` | Enriches board with display/review context. |
| Sort helper | `src/services/draft_day_app_v1_service.py::sort_rankings_frame_by_column()` | Sorts visible frames by user-selected visible columns. |
| Base full-board builder | `src/services/full_player_board_value_service.py::build_full_player_board_value_rows()` | Maps `checkpoint_review_score` into `nwr_dynasty_score` and assigns review ranks. |
| Current checkpoint | `src/services/model_v4_current_value_checkpoint_service.py::build_current_value_checkpoint()` | Intended source of `checkpoint_review_score`, but runtime receipt outputs are missing. |
| RB/WR component builder | `src/services/model_v4_rb_wr_current_value_service.py::build_rb_wr_current_value()` | Produces review-only RB/WR component scores when receipts exist. |
| QB/TE component builder | `src/services/model_v4_qb_te_current_value_service.py::build_qb_te_current_value()` | Produces review-only QB/TE component scores when receipts exist. |
| Replacement/VORP builder | `src/services/model_v4_replacement_vorp_core_service.py::build_replacement_vorp_core()` | Produces review-only replacement/VORP base points when receipts exist. |
| Lifecycle builder | `src/services/model_v4_lifecycle_archetype_service.py` | Produces lifecycle modifier receipts when present. |
| Confidence builder | `src/services/model_v4_confidence_missingness_service.py` | Produces confidence cap/missingness receipts when present. |
| Candidate overlay | `src/services/model_v4_wr_qb_v2_candidate_service.py::build_wr_qb_v2_candidate()` | Applies WR/QB v2 candidate review-only overlay and policy stamps. |

## Required Inputs

Exact current or historical formula replay requires source-traced receipts for:

- Canonical player identity and position.
- NWR league scoring points, including non-PPR and first-down scoring.
- Replacement baselines and VORP points by position.
- RB/WR/QB/TE position-specific component inputs.
- Lifecycle/archetype modifier inputs.
- Confidence and missingness cap inputs.
- Candidate overlay inputs only if the candidate overlay is the explicitly approved target.
- Row-level allowed-use, blocked-use, warning, and source-policy fields.

## Excluded Inputs

The following are excluded from active production formula status unless separately admitted:

- Market/ADP/DynastyProcess fields.
- Outcome labels and future finish fields.
- Injury/availability fields without decision-date receipts.
- NGS/PFR/CFBD advanced context without model-use gates.
- Candidate overlay fields while `candidate_review_only_not_active_rankings` remains in force.
- Any target-season or future-season data for historical replay.

## Output Schema

Minimum active formula output schema before production-active use:

- `player_id`
- `canonical_player_key`
- `player_name`
- `position`
- `nwr_rank`
- `nwr_dynasty_score`
- `score_status`
- `trust_status`
- `source_path`
- `source_column`
- `upstream_source_path`
- `upstream_source_column`
- `model_version`
- `score_type`
- `score_as_of_date`
- `allowed_use`
- `blocked_use`
- `warning_flags`
- `evidence_fields_used`
- receipt/checkpoint identifier fields sufficient to reconcile the score.

## Required Source Gates

Before the formula can be called production-active, each component must have:

- A documented source gate admitting the field for model use.
- A decision-date safety statement.
- Identity join policy and collision handling.
- Missingness semantics.
- Leakage review.
- Receipt rows sufficient to reproduce raw value, normalized value, weight, cap, contribution, and final reconciliation.

## Required Receipts

The minimum current receipt chain:

1. Replacement/VORP player, component, receipt, and warning files.
2. RB/WR component rows, receipts, and warnings.
3. QB/TE component rows, receipts, and warnings.
4. Lifecycle component rows, receipts, and warnings.
5. Confidence/missingness rows, receipts, and warnings.
6. Current value checkpoint rows, component rows, receipts, and warnings.
7. Full-board value rows and reconciliation receipt.
8. Candidate overlay evidence and policy receipts if candidate overlay remains the selected target.

The minimum historical receipt chain is the same set, partitioned by decision season and generated only from information available before that season.

## Required Tests

- Artifact schema and row-count tests.
- Row-level policy stamp tests.
- App label/status consistency tests.
- No hidden sort tests.
- No display-only/review-only/blocked source promotion tests.
- Component contribution reconciliation tests.
- Hash/pinning tests for selected app artifact.
- Decision-date leakage tests for historical replay.
- Identity collision and missingness tests.

## Conditions Required Before Production-Active Status

Production-active status requires all of the following:

1. Human approval or documented promotion gate naming the active formula ID and active artifact.
2. Row-level `allowed_use` no longer conflicts with app presentation.
3. Complete current component receipt chain.
4. Source gates approve every production input.
5. Tests prove no blocked/display-only/review-only fields affect rank logic.
6. App labels and docs match the artifact status.

## Conditions Required Before Historical Replay

Exact historical replay requires:

1. A named formula target approved for replay.
2. Historical decision-date component receipts for every scoring component.
3. Historical labels aligned to NWR scoring and league settings.
4. Proof that no target-season/future fields are used.
5. Replay tests that reconcile component contributions to `nwr_dynasty_score`.
6. Baseline comparison plan and promotion/rejection gates defined before running the benchmark.
