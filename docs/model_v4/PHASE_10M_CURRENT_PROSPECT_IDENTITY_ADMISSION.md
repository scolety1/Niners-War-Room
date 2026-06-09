# Phase 10M Current Prospect Identity Admission

## Superseded Traceability Note

This Phase 10M checkpoint is preserved as historical traceability and is
superseded by Phase 10Q and Phase 10R. Phase 10M admitted 211 current prospects
but still treated the 21 review-only prospects as blocker warnings. Phase 10R
keeps those prospects visible for audit while making formula admission explicit:

- `formula_identity_admitted` is present on `prospect_current_feature_matrix.csv`.
- Review-only prospects have populated `excluded_reason` values.
- `admitted_prospect_current_feature_matrix.csv` contains only the 211 admitted
  formula-facing current prospects.
- Blocker warnings are now 0.
- Current status is `ready_for_formula_design_review`.

## Purpose

Phase 10M repairs the current-prospect identity admission layer before formula design. It regenerates evidence matrices, writes an admitted identity spine, and keeps unresolved prospects review-only.

## Outputs

- NFL current evidence matrix: `local_exports\model_v4\evidence_matrices\latest\nfl_player_current_evidence_matrix.csv`
- Current prospect feature matrix: `local_exports\model_v4\evidence_matrices\latest\prospect_current_feature_matrix.csv`
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
- Review-only current prospect identities: 21
- Historical rookie backtest rows: 395
- Source coverage rows: 3927
- Warning rows: 2550

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
- Blocker warnings: 21
- Historical post-draft college evidence violations: 0
- Status: review_required_before_formula_design

## Formula Safety

- ADP, rankings, cheat sheets, mock drafts, and big boards are kept in `market_context_fields_json` only.
- Projection context is not included in factual, derived, or prospect-prior evidence.
- Review-only replacement/VORP previews are kept in context fields only.
- Missing data is represented by coverage rows and warnings, not zero-filled evidence.
- Source-limited combine/pro-day rows are visible but flagged as source-limited.
- No active rankings, My Team, War Board, or readiness gates were changed.
