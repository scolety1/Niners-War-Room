# Phase 10Q Workout Missingness And Source-Lane Repair

## Purpose

Phase 10Q repairs focused source-admission issues found by the Phase 10P external pre-formula audit. It does not implement formulas, change active rankings, promote app surfaces, alter My Team or War Board, or unlock readiness gates.

## Repairs

- Impossible RotoWire workout/pro-day zero placeholders are now converted to missing values inside `workout_profile` before evidence matrices are written.
- Repaired workout profiles include `zero_placeholder_fields_repaired` and `missing_after_zero_repair` lists so formulas cannot treat unavailable tests as poor athletic performance.
- Warning rows now emit `workout_metric_zero_placeholder_repaired` and `workout_metric_missing_after_zero_repair`.
- Current prospect repaired workout profiles: 144.
- Historical rookie repaired workout profiles: 330.
- `college_production` coverage for current prospects and historical rookies is now `prospect_prior_evidence`.
- `college_market_share` coverage for current prospects and historical rookies is now `prospect_prior_evidence`.
- CFBD source status language now distinguishes redistribution-limited-but-formula-admitted-after-validation from source-limited-not-formula-admitted evidence.

## Regenerated Outputs

- `docs/model_v4/PHASE_10F_SOURCE_TRUST_CONTRACT.csv`
- `docs/model_v4/PHASE_10F_SOURCE_TRUST_CONTRACT.md`
- `docs/model_v4/PHASE_10N_EVIDENCE_ADMISSION_RECHECK.md`
- `local_exports/model_v4/evidence_matrices/latest/prospect_current_feature_matrix.csv`
- `local_exports/model_v4/evidence_matrices/latest/historical_rookie_backtest_feature_matrix.csv`
- `local_exports/model_v4/evidence_matrices/latest/source_coverage_matrix.csv`
- `local_exports/model_v4/evidence_matrices/latest/warning_matrix.csv`
- `local_exports/model_v4/evidence_matrices/latest/evidence_matrix_summary.csv`

## QA Results

- Workout zero placeholder violations: 0.
- Market leakage violations: 0.
- Duplicate entity rows: 0.
- Fake-zero missing violations: 0.
- Ambiguous join rows: 0.
- Historical post-draft college evidence violations: 0.
- Phase 10N admission recheck: pass, 14 checks, 0 issues.

## Remaining Quarantine

The 21 review-only current prospects remain intentionally blocked from the admitted identity spine. This phase did not resolve Phase 10R-style formula-facing matrix quarantine work; formulas still must fail closed unless identity admission is explicit.
