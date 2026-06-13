# Sprint 5AY Partial Threshold Model Evaluation

## Status

Verdict: `EXACT_PERCENTAGES_NOT_READY`

Sprint 5AY ran a local, internal-only release-candidate evaluation for same-year 2026 veteran threshold outcome heads. The run used historical 2020-2024 threshold labels, a train/validation/test split of 2020-2022 / 2023 / 2024, and the 520 ready 2026 veteran feature rows from the recovery and identity-repair sprints.

No app wiring, app-readable probability table, ranking/sorting change, fake probability, promoted model artifact, deployment, or push occurred.

## Inputs

- Historical rows evaluated: 2,118
- Train rows, 2020-2022: 1,291
- Validation rows, 2023: 412
- Test rows, 2024: 415
- Current ready 2026 veteran rows scored for internal audit only: 520
- Current blocked 2026 veteran rows not scored: 172
- Top-priority waived players still not scored: 5
- Rookie rows excluded for separate rookie path: 80
- Kicker rows not applicable: 8

Historical labels were built from `position_rank` in the historical label linkage files. This is a direct threshold-rank fallback for this audit, not a promoted probability-release label artifact.

## Method

- Evaluated same-year threshold heads only.
- Used veteran path only.
- Used renamed legal prior-completed-season features only.
- Excluded rookies from the veteran model path.
- Excluded kickers as not applicable.
- Excluded blocked and waived current players from 2026 scoring.
- Used simple regularized logistic models where train support allowed two-class training.
- Used empirical fallback only where required by support constraints.
- Did not apply calibration, isotonic repair, gradient boosting, stacking, monotonic repair, artifact promotion, or app output generation.

Forbidden-field scan passed for the evaluated feature set. No ADP, public rankings, projections, market values, trade values, prior fantasy draft history, RotoWire projections/rankings/outlooks/values, legacy `private_score`, same-season final stats, or label supplement sources were used as prediction features.

## Local Exports

Created under `local_exports/outcome_probability/sprint_5ay_partial_threshold_model_evaluation/`:

- `threshold_head_support.csv`
- `threshold_head_validation_metrics.csv`
- `threshold_head_calibration_audit.csv`
- `threshold_head_monotonicity_audit.csv`
- `partial_2026_veteran_prediction_audit_internal_only.csv`
- `coverage_warning_audit.csv`
- `threshold_release_decision_table.csv`
- `blocked_threshold_heads.csv`
- `forbidden_feature_scan.csv`
- `metadata_sprint_5ay.json`
- `README_SPRINT_5AY.md`

The player-level export is explicitly internal-only and not app-readable. It includes blocked display/sorting/release flags and must not be wired into the application.

## Threshold Head Support

| Target | Historical rows | Events | Non-events | Train events | Validation events | Test events | Sparse |
|---|---:|---:|---:|---:|---:|---:|---|
| `same_year_qb_t6` | 307 | 29 | 278 | 18 | 6 | 5 | yes |
| `same_year_qb_t12` | 307 | 56 | 251 | 35 | 11 | 10 | no |
| `same_year_qb_t18` | 307 | 84 | 223 | 52 | 17 | 15 | no |
| `same_year_qb_t24` | 307 | 111 | 196 | 69 | 22 | 20 | no |
| `same_year_rb_t6` | 538 | 28 | 510 | 16 | 6 | 6 | yes |
| `same_year_rb_t12` | 538 | 54 | 484 | 33 | 10 | 11 | no |
| `same_year_rb_t24` | 538 | 103 | 435 | 59 | 22 | 22 | no |
| `same_year_rb_t36` | 538 | 159 | 379 | 92 | 33 | 34 | no |
| `same_year_rb_t48` | 538 | 204 | 334 | 118 | 42 | 44 | no |
| `same_year_wr_t6` | 817 | 26 | 791 | 16 | 5 | 5 | yes |
| `same_year_wr_t12` | 817 | 54 | 763 | 34 | 11 | 9 | no |
| `same_year_wr_t24` | 817 | 106 | 711 | 64 | 21 | 21 | no |
| `same_year_wr_t36` | 817 | 155 | 662 | 94 | 30 | 31 | no |
| `same_year_wr_t48` | 817 | 209 | 608 | 127 | 40 | 42 | no |
| `same_year_te_t3` | 456 | 13 | 443 | 9 | 2 | 2 | yes |
| `same_year_te_t6` | 456 | 28 | 428 | 18 | 5 | 5 | yes |
| `same_year_te_t12` | 456 | 56 | 400 | 34 | 11 | 11 | no |
| `same_year_te_t18` | 456 | 84 | 372 | 51 | 16 | 17 | no |
| `same_year_te_t24` | 456 | 113 | 343 | 68 | 22 | 23 | no |

## Validation And Test Metrics

All 19 heads produced evaluation metrics, but all heads also had unstable calibration bins. Positive Brier improvement versus baseline is not sufficient for app release because calibration stability, threshold-chain monotonicity, and release-gate standards are not met.

| Target | Validation Brier | Test Brier | Validation Brier improvement | Test Brier improvement | Calibration status |
|---|---:|---:|---:|---:|---|
| `same_year_qb_t6` | 0.070537 | 0.055719 | 0.015649 | 0.017751 | unstable bins present |
| `same_year_qb_t12` | 0.118438 | 0.106661 | 0.026031 | 0.028074 | unstable bins present |
| `same_year_qb_t18` | 0.150059 | 0.135803 | 0.047273 | 0.048023 | unstable bins present |
| `same_year_qb_t24` | 0.180114 | 0.161075 | 0.048171 | 0.059669 | unstable bins present |
| `same_year_rb_t6` | 0.046973 | 0.052075 | 0.006503 | 0.005579 | unstable bins present |
| `same_year_rb_t12` | 0.080124 | 0.080881 | 0.005335 | 0.018945 | unstable bins present |
| `same_year_rb_t24` | 0.147856 | 0.122885 | 0.017570 | 0.053499 | unstable bins present |
| `same_year_rb_t36` | 0.155485 | 0.154269 | 0.060202 | 0.077414 | unstable bins present |
| `same_year_rb_t48` | 0.170237 | 0.166076 | 0.070837 | 0.090477 | unstable bins present |
| `same_year_wr_t6` | 0.027448 | 0.027990 | 0.003965 | 0.001746 | unstable bins present |
| `same_year_wr_t12` | 0.054601 | 0.043720 | 0.011737 | 0.008609 | unstable bins present |
| `same_year_wr_t24` | 0.073445 | 0.076342 | 0.044394 | 0.035895 | unstable bins present |
| `same_year_wr_t36` | 0.080609 | 0.096814 | 0.076293 | 0.057205 | unstable bins present |
| `same_year_wr_t48` | 0.089855 | 0.111248 | 0.102453 | 0.080041 | unstable bins present |
| `same_year_te_t3` | 0.025420 | 0.030248 | -0.003350 | -0.008640 | unstable bins present |
| `same_year_te_t6` | 0.045178 | 0.053948 | 0.007927 | -0.001917 | unstable bins present |
| `same_year_te_t12` | 0.073736 | 0.100317 | 0.034584 | 0.005955 | unstable bins present |
| `same_year_te_t18` | 0.096420 | 0.111366 | 0.051061 | 0.040552 | unstable bins present |
| `same_year_te_t24` | 0.116574 | 0.123579 | 0.069515 | 0.065328 | unstable bins present |

## Calibration Findings

Calibration status: `unstable_bins_present` for every evaluated head.

No calibration layer was fit or promoted. No isotonic calibration was applied. The bin-level audit is useful for research triage but is not stable enough to justify exact player-facing percentages.

## Monotonicity Findings

| Position | Rows checked | Rows with violation | Violation rate | Max adjacent gap | Adjacent violation counts | Status |
|---|---:|---:|---:|---:|---|---|
| QB | 74 | 0 | 0.000000 | 0.000000 |  | pass |
| RB | 125 | 3 | 0.024000 | 0.012789 | `same_year_rb_t36>same_year_rb_t48:3` | fail |
| WR | 201 | 15 | 0.074627 | 0.002894 | `same_year_wr_t12>same_year_wr_t24:15`; `same_year_wr_t6>same_year_wr_t12:12` | fail |
| TE | 120 | 0 | 0.000000 | 0.000000 |  | pass |

RB and WR threshold chains failed monotonicity. No monotonic repair was applied. Exact percentage release remains blocked.

## Release Decision Table

| Recommendation | Heads |
|---|---|
| `blocked_sparse_events` | `same_year_qb_t6`, `same_year_rb_t6`, `same_year_wr_t6`, `same_year_te_t3`, `same_year_te_t6` |
| `blocked_unstable_calibration` | `same_year_qb_t12`, `same_year_qb_t18`, `same_year_qb_t24`, `same_year_te_t12`, `same_year_te_t18`, `same_year_te_t24` |
| `coarse_band_research_only` | `same_year_rb_t12`, `same_year_rb_t24`, `same_year_rb_t36`, `same_year_rb_t48`, `same_year_wr_t12`, `same_year_wr_t24`, `same_year_wr_t36`, `same_year_wr_t48` |

No exact percentages are ready to release.

Coarse bands are not app-ready. The eight `coarse_band_research_only` heads may be considered for further internal adversarial review only. They are not approved for player detail display, rankings table display, sorting, automation, release-gate promotion, or public/app-facing use.

## Coverage Warning Audit

| Coverage item | Count | Status |
|---|---:|---|
| Ready 2026 veteran feature rows | 520 | scored internal-only |
| Blocked 2026 veteran feature rows | 172 | not scored |
| Top-priority waived players missing features | 5 | not scored; waived for partial training only |
| Rookie rows | 80 | excluded for separate path |
| Kicker rows | 8 | not applicable |
| Player-level output rows | 2,526 | internal-only; not released |
| App probability files created | 0 | none |
| Promoted model artifacts created | 0 | none |

The five waived players from Sprint 5AX-R remain unscored because they still lack usable 2025 veteran feature rows. The waiver allowed partial training/evaluation to proceed; it did not create or impute valid 2026 features.

## Final Recommendation

Recommendation: `KEEP_INTERNAL_ONLY_AND_RUN_5AZ`

Sprint 5AY establishes that partial veteran threshold evaluation can run and produce useful internal audit artifacts. It does not establish enough calibration stability, monotonicity readiness, or support quality for exact percentages. It also does not approve coarse bands for app display.

Sprint 5AZ should run next as an adversarial audit of the internal-only heads, especially the eight coarse-band research candidates and the RB/WR monotonicity failures. App wiring should not start yet.

## Explicit Non-Actions

- No app probabilities were created.
- No fake or placeholder probabilities were created.
- No calibrated probabilities were promoted.
- No player-facing probabilities were created.
- No app-readable probability tables were created.
- No rankings or sorting changes were made.
- No decision automation was created.
- No model artifact was promoted.
- No app wiring, push, or deploy occurred.
