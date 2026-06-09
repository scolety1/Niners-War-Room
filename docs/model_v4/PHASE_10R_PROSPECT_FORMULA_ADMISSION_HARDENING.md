# Phase 10R Prospect Formula Admission Hardening

## Purpose

Phase 10R hardens current-prospect formula admission before formula design. It writes explicit formula identity admission flags onto the full prospect matrix, creates an admitted-only prospect feature matrix, and keeps unresolved prospects visible for review but unavailable to formula scoring.

## Outputs

- NFL current evidence matrix: `local_exports\model_v4\evidence_matrices\latest\nfl_player_current_evidence_matrix.csv`
- Current prospect feature matrix: `local_exports\model_v4\evidence_matrices\latest\prospect_current_feature_matrix.csv`
- Admitted prospect feature matrix: `local_exports\model_v4\evidence_matrices\latest\admitted_prospect_current_feature_matrix.csv`
- Historical rookie backtest feature matrix: `local_exports\model_v4\evidence_matrices\latest\historical_rookie_backtest_feature_matrix.csv`
- Source coverage matrix: `local_exports\model_v4\evidence_matrices\latest\source_coverage_matrix.csv`
- Warning matrix: `local_exports\model_v4\evidence_matrices\latest\warning_matrix.csv`
- Admitted prospect identity spine: `local_exports\model_v4\evidence_matrices\latest\admitted_current_prospect_identity_spine.csv`
- Prospect identity review report: `local_exports\model_v4\evidence_matrices\latest\current_prospect_identity_review_report.csv`
- Prospect identity admission notes: `local_exports\model_v4\evidence_matrices\latest\current_prospect_identity_admission_notes.csv`
- Summary: `local_exports\model_v4\evidence_matrices\latest\evidence_matrix_summary.csv`

## Row Counts

- NFL current players: 80
- Current prospects: 232
- Admitted current prospect identities: 211
- Admitted prospect feature rows: 211
- Review-only current prospect identities: 21
- Historical rookie backtest rows: 395
- Source coverage rows: 3927
- Warning rows: 1706

## Admission Repair Notes

- Blank current-prospect college/team values are backfilled from later source records only when the exact normalized name and position key match.
- `Nick Singleton` is explicitly aliased to `Nicholas Singleton` because Penn State RB evidence aligns across board, market, RotoWire, and CFBD sources.
- Generic `player_id` values are namespaced by source family so CFBD and RotoWire IDs do not create false same-namespace conflicts.
- Recruiting positions remain prospect-prior context but no longer veto current-position admission by themselves.
- Transfer/team mismatches remain quarantined unless source compatibility is clear.

## Remaining Review-Only Reasons

- insufficient_identity_support: 12
- position_conflict: 9

## QA

- Duplicate entity rows: 0
- Market leakage violations: 0
- Fake-zero missing violations: 0
- Ambiguous join rows: 0
- Blocker warnings: 0
- Historical post-draft college evidence violations: 0
- Status: ready_for_formula_design_review

## Formula Safety

- Formula loaders must fail closed unless `formula_identity_admitted == True`.
- Review-only prospects have populated `excluded_reason` values.
- `admitted_prospect_current_feature_matrix.csv` contains only admitted rows.
- ADP, rankings, cheat sheets, mock drafts, and big boards are kept in `market_context_fields_json` only.
- Projection context is not included in factual, derived, or prospect-prior evidence.
- Review-only replacement/VORP previews are kept in context fields only.
- Missing data is represented by coverage rows and warnings, not zero-filled evidence.
- Source-limited combine/pro-day rows are visible but flagged as source-limited.
- No active rankings, My Team, War Board, or readiness gates were changed.
