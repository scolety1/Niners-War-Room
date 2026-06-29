# Rookie Outcome R&D Repo Inventory - 2026-06-29

## Actual Base HEAD

Base branch: `origin/work/hq-parallel-control`

Actual base HEAD: `99995fd4cfc6ebfc7e3f70b8eaba4cba8421339d`

Feature branch: `work/rookie-outcome-rd-20260629`

## Scope Decision

This lane is R&D, audit, specification, and blocker mapping only.

No rookie probabilities, rookie model scores, Rankings columns, source-truth promotion, CFBD model input, or CFBD training truth were created.

## Relevant CFBD Files Found

- `docs/hq/data_sources/cfbd_review_artifacts_20260624/README.md`
- `docs/hq/data_sources/cfbd_review_artifacts_20260624/cfbd_pull_manifest.csv`
- `docs/hq/data_sources/cfbd_review_artifacts_20260624/cfbd_player_identity_review_queue.csv`
- `docs/hq/data_sources/cfbd_review_artifacts_20260624/cfbd_player_production_review.csv`
- `docs/hq/data_sources/cfbd_review_artifacts_20260624/cfbd_coverage_report.csv`
- `docs/hq/data_sources/cfbd_review_artifacts_20260624/cfbd_data_dictionary.csv`
- `docs/hq/data_sources/cfbd_identity_matching_v1_20260624/README.md`
- `docs/hq/data_sources/cfbd_identity_matching_v1_20260624/cfbd_identity_high_confidence_review.csv`
- `docs/hq/data_sources/cfbd_identity_matching_v1_20260624/cfbd_identity_possible_review.csv`
- `docs/hq/data_sources/cfbd_identity_matching_v1_20260624/cfbd_identity_ambiguous_review.csv`
- `docs/hq/data_sources/cfbd_identity_matching_v1_20260624/cfbd_identity_unmatched_priority_review.csv`
- `docs/hq/data_sources/cfbd_identity_matching_v1_20260624/cfbd_identity_link_registry_DRAFT.csv`
- `docs/hq/data_sources/cfbd_identity_matching_v1_20260624/cfbd_identity_production_context_review.csv`
- `docs/hq/data_sources/cfbd_identity_matching_v1_20260624/cfbd_identity_review_dashboard_summary.csv`
- `docs/hq/data_sources/cfbd_identity_matching_v1_20260624/cfbd_identity_final_review_method.md`

## CFBD Counts Observed

- CFBD source identity rows: 31,822
- High-confidence exact review rows: 157
- Possible/ambiguous rows: 56
- Draft link registry rows: 213
- Unmatched priority rows: 31,614
- Production-context review rows: 5,817
- CFBD production artifact rows: 16,938
- CFBD pull/coverage rows: 18

Every inspected CFBD artifact keeps `model_use_allowed=false` and `training_allowed=false`. The draft link registry keeps `approved_by_human=false`.

## Relevant Identity Files Found

- `docs/hq/data_sources/identity/player_id_coverage_audit_v1.csv`
- `docs/hq/data_sources/identity/player_identity_manual_review_queue_v1.csv`
- `docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_consolidated_review.csv`
- `docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_identity_triage.csv`
- `docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_identity_gap_review.csv`
- `docs/hq/review_queue/full_refresh_stats_completion_20260626/unified_missing_id_resolution_decisions.csv`

The latest full-refresh completion queue keeps five unified missing-ID rows blocked. Missing identity cannot become rookie outcome truth.

## Relevant Draft Capital Files Found

- `docs/model_v4/ROOKIE_DRAFT_CAPITAL_2026_SNAPSHOT.md`
- `src/services/model_v4_draft_capital_snapshot_service.py`
- `tests/test_model_v4_draft_capital_snapshot_service.py`
- `templates/real_data_inputs/historical_rookie_replay/pre_draft_prospect_inputs.csv`
- `templates/real_data_inputs/historical_rookie_replay/post_draft_outcomes.csv`
- `sample_data/historical_rookie_replay/pre_draft_prospect_inputs.csv`
- `sample_data/historical_rookie_replay/post_draft_outcomes.csv`

The 2026 draft-capital snapshot is documented as 257 rows, but the processed artifact path lives under `local_exports`, which must not be tracked or used as durable source truth in this lane. Historical rookie replay templates are empty. Sample data exists but is sample/test context, not production training truth.

## Relevant Historical Rookie / NFL Outcome Files Found

- `src/services/model_v4_rookie_outcome_label_service.py`
- `tests/test_model_v4_rookie_outcome_label_service.py`
- `src/services/model_v4_historical_rookie_tuning_service.py`
- `src/services/historical_rookie_replay_service.py`
- `docs/model_v4/MODEL_V4_3_4_HISTORICAL_ROOKIE_TUNING_TAB.md`
- `docs/model_v4/MODEL_V4_3_6_ROOKIE_REPLAY_BASELINE_COMPARISON.md`
- `docs/model_v4/MODEL_V4_3_6_ROOKIE_CALIBRATION_CANDIDATE_PLAN.md`
- `docs/model_v4/MODEL_V4_3_5_DEEP_RESEARCH_ROOKIE_CALIBRATION_INTAKE.md`
- `docs/model_v4/MODEL_V4_3_5_SECOND_ROOKIE_REPLAY_AUDIT_INTAKE.md`
- `docs/model_v4/MODEL_V4_3_5_THIRD_ROOKIE_REPLAY_AUDIT_INTAKE.md`

These files show useful prior research, but the historical rookie outcome label service depends on `local_exports/model_v4/rotowire_intake/latest/rotowire_player_stats_clean_rows.csv`. That is not an approved tracked model/training source for this R&D lane.

## Relevant Source-Policy Docs Found

- `docs/hq/data_sources/cfbd_identity_matching_v1_20260624/cfbd_identity_final_review_method.md`
- `docs/hq/parallel_lanes/NWR_CFBD_IDENTITY_MATCHING_V1_20260624.md`
- `docs/hq/audits/agent_audit_synthesis_20260626/05_CFBD_REVIEW_ONLY_SYNTHESIS.md`
- `docs/hq/review_queue/full_refresh_stats_completion_20260626/full_refresh_stats_completion_gate.csv`
- `docs/hq/integration/evidence_status_registry_v1_20260626.csv`

The policy thread is consistent: CFBD remains review-only, not model input, not training truth, and not source truth.

## Missing Or Blocked Files

- No approved human-reviewed CFBD identity approval artifact was found.
- No approved tracked rookie draft-capital artifact covering historical and current classes was found.
- No approved historical rookie label dataset for rookie-year, year-2, first-3-year, or first-5-year thresholds was found.
- No approved current rookie/prospect outcome probability artifact was found.
- One prior review CSV, `docs/hq/review_queue/full_refresh_stats_completion_20260626/cfbd_ambiguous_identity_decisions.csv`, does not parse cleanly with the default CSV parser and should be treated as a review-queue artifact needing repair, not as machine truth.

## Current Guardrail Status

No protected/model/rank/source-truth files were touched in Phase 0.

Current safe conclusion: a full rookie outcome build is not yet supported by approved/local data. A future build requires identity approval, draft-capital approval, historical label approval, and source-policy gates.
