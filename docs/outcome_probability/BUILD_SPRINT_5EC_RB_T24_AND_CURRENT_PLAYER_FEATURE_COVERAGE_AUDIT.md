# Sprint 5EC - RB Top 24 And Current Player Feature Coverage Audit

## Purpose

Sprint 5EC audits whether the HQ-requested `rb_t24` head can be included in a quarantined local-only numeric probability dry run and whether the Rankings page player pool has enough current-player feature coverage for the Phase 10 target heads.

This sprint does not emit probabilities, create app-readable artifacts, edit app/source files, wire UI display, change rankings/sorting, create hidden sort keys, create promoted artifacts, push, deploy, or release.

## Inputs

Read-only evidence:

- `docs/outcome_probability/BUILD_SPRINT_5DA_PHASE_6_LOCAL_ONLY_PRODUCTION_CANDIDATE_MODELING.md`
- `docs/outcome_probability/BUILD_SPRINT_5DB_PHASE_6_PRODUCTION_CANDIDATE_CALIBRATION_SANITY_AUDIT.md`
- `local_exports/outcome_probability/sprint_5cu_phase5_local_candidate_model_evaluation/head_candidate_verdicts.csv`
- `local_exports/outcome_probability/sprint_5da_phase6_local_only_production_candidate_modeling/head_candidate_verdicts.csv`
- `local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv`
- `local_exports/outcome_probability/sprint_5aw_2026_identity_repair/current_2026_veteran_feature_snapshots_after_identity_repair.csv`

Local-only 5EC evidence:

`local_exports/outcome_probability/phase10_numeric_probability_display_runway/sprint_5ec_current_player_feature_coverage/`

Files:

- `current_player_feature_coverage_summary.json`
- `current_player_feature_coverage_rows.csv`

These outputs are local-only evidence and are not app-readable production artifacts.

## Phase 6 Accepted Heads Versus HQ Target Heads

Phase 6 accepted heads:

- `qb_t12`
- `rb_t12`
- `wr_t12`
- `wr_t24`
- `wr_t36`
- `te_t12`

HQ Phase 10 target heads:

- `qb_t12`
- `rb_t12`
- `rb_t24`
- `wr_t12`
- `wr_t24`
- `wr_t36`
- `te_t12`

The only delta is `rb_t24`.

## RB Top 24 Gate

`rb_t24` was excluded from Phase 6 as a caution head, but Phase 5 local-only candidate evidence showed:

| Metric | Value |
| --- | ---: |
| Phase 5 verdict | `candidate_caution` |
| Mean AUC | 0.833113 |
| Mean Brier | 0.120540 |
| Base Brier | 0.161677 |
| Mean log loss | 0.387880 |
| Base log loss | 0.504422 |
| Thin calibration bins | 7 |

Decision: `rb_t24` is GREEN-upgraded for Sprint 5ED local-only dry-run inclusion only.

This is not a display-release approval. The head still carries calibration caution, and any later app/display proposal must keep the Phase 5 caution history visible.

## Current-Player Feature Coverage

The Rankings full-board pool had 240 observed rows. The repaired 2026 veteran feature snapshot source had 520 ready rows. Joining the Rankings pool by `player_id` to current feature snapshots produced:

| Position | Rankings rows | Feature-ready rows | Not ready rows |
| --- | ---: | ---: | ---: |
| QB | 28 | 28 | 0 |
| RB | 79 | 76 | 3 |
| WR | 93 | 91 | 2 |
| TE | 32 | 32 | 0 |
| K | 8 | 0 | 8 |

Rookie rows observed in the current full-board pool: 0.

Unsupported position rows: 8 K rows.

## Missing Feature Handling

Rows without a ready current feature snapshot, rows missing any required prior-season feature, rookies, kickers, and unsupported positions must be unavailable in any local-only dry run.

They must not receive fake `0%` values. They must not be carried as hidden sort/ranking fields.

## Required Feature Allowlist

The 5EC audit requires the current dry-run feature source to provide:

- `prior_season_nwr_ppg`
- `prior_season_nwr_finish_rank`
- `prior_completed_season_games`
- `prior_completed_season_games_played`
- `prior_completed_season_games_active`
- `prior_completed_season_passing_yards`
- `prior_completed_season_rushing_yards`
- `prior_completed_season_receiving_yards`
- `prior_completed_season_rushing_first_downs`
- `prior_completed_season_receiving_first_downs`
- `prior_completed_season_receptions`

Forbidden fields remain quarantined, including ADP, public rankings, projections, consensus, market values, trade values/calculators, RotoWire rankings/projections/outlooks/values, prior fantasy draft history, legacy `private_score`, fantasy totals, EPA, WOPR/RACR/PACR/Dakota, target-share fields, same-season target stats as preseason features, and label supplement sources as prediction features.

## Approved Heads For Sprint 5ED Local-Only Dry Run

Approved local-only dry-run heads:

- `qb_t12`
- `rb_t12`
- `rb_t24`
- `wr_t12`
- `wr_t24`
- `wr_t36`
- `te_t12`

`rb_t24` is included only because 5EC explicitly upgraded it for the local dry run based on Phase 5 metric improvement and sufficient current RB feature coverage. It remains blocked for app display until later gates pass.

## No-Probability Confirmation

Sprint 5EC emitted no probabilities, no app-readable artifact, no exact display percentages, no coarse bands, no app wiring, no rankings/sorting changes, no hidden sort keys, and no promoted artifacts.

## Recommendation

Verdict: GREEN for Sprint 5ED local-only current-player probability dry run.

Proceed with the seven approved heads above. Missing-feature, rookie, kicker, and unsupported rows must be unavailable. The 5ED dry run must remain quarantined under `local_exports/` and must not create app-readable generated output.
