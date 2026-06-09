# Phase 10G Evidence Matrices

## Superseded Traceability Note

This Phase 10G checkpoint is preserved as historical traceability and is
superseded by:

- `docs/model_v4/PHASE_10Q_WORKOUT_MISSINGNESS_AND_SOURCE_LANE_REPAIR.md`
- `docs/model_v4/PHASE_10R_PROSPECT_FORMULA_ADMISSION_HARDENING.md`
- `docs/model_v4/PHASE_10N_EVIDENCE_ADMISSION_RECHECK.md`

The row counts below are stale because later phases repaired workout
missingness, source-lane labels, and prospect formula admission. The current
Phase 10R state is:

- Current prospects: 232
- Admitted prospect identities: 211
- Admitted prospect feature rows: 211
- Review-only prospects: 21
- Source coverage rows: 3927
- Warning rows: 2550
- Blocker warnings: 0
- Status: `ready_for_formula_design_review`

Formula-facing prospect features must use
`local_exports/model_v4/evidence_matrices/latest/admitted_prospect_current_feature_matrix.csv`,
not the full review matrix.

## Purpose

Phase 10G creates formula-ready evidence matrices without calculating final rankings, final Dynasty Asset Value, or promotion scores.

## Outputs

- NFL current evidence matrix: `local_exports\model_v4\evidence_matrices\latest\nfl_player_current_evidence_matrix.csv`
- Current prospect feature matrix: `local_exports\model_v4\evidence_matrices\latest\prospect_current_feature_matrix.csv`
- Historical rookie backtest feature matrix: `local_exports\model_v4\evidence_matrices\latest\historical_rookie_backtest_feature_matrix.csv`
- Source coverage matrix: `local_exports\model_v4\evidence_matrices\latest\source_coverage_matrix.csv`
- Warning matrix: `local_exports\model_v4\evidence_matrices\latest\warning_matrix.csv`
- Admitted prospect identity spine: `local_exports\model_v4\evidence_matrices\latest\admitted_current_prospect_identity_spine.csv`
- Prospect identity review report: `local_exports\model_v4\evidence_matrices\latest\current_prospect_identity_review_report.csv`
- Summary: `local_exports\model_v4\evidence_matrices\latest\evidence_matrix_summary.csv`

## Row Counts

- NFL current players: 80
- Current prospects: 233
- Admitted current prospect identities: 201
- Review-only current prospect identities: 32
- Historical rookie backtest rows: 395
- Source coverage rows: 3933
- Warning rows: 1842

## QA

- Duplicate entity rows: 0
- Market leakage violations: 0
- Fake-zero missing violations: 0
- Ambiguous join rows: 0
- Blocker warnings: 32
- Historical post-draft college evidence violations: 0
- Status: review_required_before_formula_design

## Formula Safety

- ADP, rankings, cheat sheets, mock drafts, and big boards are kept in `market_context_fields_json` only.
- Projection context is not included in factual, derived, or prospect-prior evidence.
- Review-only replacement/VORP previews are kept in context fields only.
- Missing data is represented by coverage rows and warnings, not zero-filled evidence.
- Source-limited combine/pro-day rows are visible but flagged as source-limited.
- No active rankings, My Team, War Board, or readiness gates were changed.
