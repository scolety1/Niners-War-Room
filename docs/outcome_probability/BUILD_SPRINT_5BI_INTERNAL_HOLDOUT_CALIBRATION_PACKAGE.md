# Sprint 5BI Internal Holdout Calibration Package

## 1. Executive verdict

Verdict: `INTERNAL_HOLDOUT_CALIBRATION_RESEARCH_ONLY_BLOCKED_FOR_RELEASE`

Sprint 5BI generated an internal-only holdout calibration package for the RB/WR constrained threshold prototype. The package can now honestly compare:

1. Raw independent baseline.
2. Post-hoc forward clamped benchmark.
3. Constrained/PAVA candidate.

Adjusted validation/test prediction rows were generated from existing legal 5X/5N historical feature and label artifacts. The constrained/PAVA candidate again clears the top-N-or-better monotonicity gate and has slightly better average Brier/log-loss than the raw and clamped methods on these holdout splits.

Release remains blocked. Every method still has unstable calibration bins on all 10 RB/WR heads across validation and test. Exact percentages, coarse bands, app wiring, rankings/sorting, and promoted artifacts remain blocked.

## 2. Files/artifacts created

Code created:

- `scripts/outcome_probability/build_sprint_5bi_internal_holdout_calibration_package.py`

Report created:

- `docs/outcome_probability/BUILD_SPRINT_5BI_INTERNAL_HOLDOUT_CALIBRATION_PACKAGE.md`

Local-only exports created under:

`local_exports/outcome_probability/sprint_5bi_internal_holdout_calibration_package/`

Created export files:

- `artifact_quarantine_audit.csv`
- `calibration_bins.csv`
- `calibration_bin_stability.csv`
- `coverage_audit.csv`
- `forbidden_feature_scan.csv`
- `holdout_predictions_internal_only.csv`
- `metadata_sprint_5bi.json`
- `monotonicity_audit.csv`
- `population_policy_audit.csv`
- `raw_clamped_constrained_metric_comparison.csv`
- `README_SPRINT_5BI.md`
- `release_blockers.csv`
- `sparse_head_audit.csv`
- `split_discipline_audit.csv`

All local-only exports are marked `internal_only_not_app_readable` or `blocked_not_app_readable`. They must not be committed.

## 3. Source artifacts and split discipline

5BI used existing legal historical artifacts only:

- Train: 2020-2022 from `local_exports/outcome_probability/sprint_5x_2020_2022_historical_rebuild/`
- Validation: 2023 from `local_exports/outcome_probability/sprint_5n_broader_historical_rebuild/`
- Test: 2024 from `local_exports/outcome_probability/sprint_5n_broader_historical_rebuild/`

Split discipline audit:

| Gate | Status | Evidence |
|---|---|---|
| Train/validation/test split | pass | Train 834 RB/WR rows; validation 260 RB/WR rows; test 261 RB/WR rows |
| Same-season final stats as features | pass | 5X/5N feature snapshots use completed prior-season feature lineage |

Same-season outcomes are used only as holdout labels.

## 4. Adjusted validation/test prediction rows

Adjusted holdout prediction rows were generated successfully.

| Row type | Count | Scope |
|---|---:|---|
| Raw independent baseline rows | 2,605 | internal-only validation/test rows |
| Adjusted clamped/constrained rows | 5,210 | internal-only validation/test rows |
| Total prediction rows | 7,815 | not app-readable, not sortable, not player-facing |

Every prediction row includes:

- `exact_percentage_display_allowed=no`
- `coarse_band_display_allowed=no`
- `sort_allowed=no`
- `ranking_use_allowed=no`
- `app_readable=no`

## 5. Raw vs clamped vs constrained metric summary

Average metric summary across the 10 RB/WR heads:

| Split | Method | Average Brier | Average log loss |
|---|---|---:|---:|
| Validation | Raw independent baseline | 0.096871 | 0.310235 |
| Validation | Post-hoc forward clamp benchmark | 0.097012 | 0.310614 |
| Validation | Constrained/PAVA candidate | 0.096857 | 0.310188 |
| Test | Raw independent baseline | 0.095936 | 0.307181 |
| Test | Post-hoc forward clamp benchmark | 0.095949 | 0.307363 |
| Test | Constrained/PAVA candidate | 0.095883 | 0.307038 |

Finding:

- Constrained/PAVA is slightly best on average Brier/log-loss for both validation and test.
- Clamping is slightly worse than raw on average in this holdout package.
- Differences are small and do not clear release gates.
- No calibration layer was fit or promoted.

## 6. Calibration-bin stability

Calibration-bin stability result: blocked.

| Split | Method | Unstable heads | Total heads | Max absolute calibration gap | Minimum bin events |
|---|---|---:|---:|---:|---:|
| Validation | Raw independent baseline | 10 | 10 | 0.350186 | 0 |
| Validation | Post-hoc forward clamp benchmark | 10 | 10 | 0.350186 | 0 |
| Validation | Constrained/PAVA candidate | 10 | 10 | 0.350186 | 0 |
| Test | Raw independent baseline | 10 | 10 | 0.272990 | 0 |
| Test | Post-hoc forward clamp benchmark | 10 | 10 | 0.272990 | 0 |
| Test | Constrained/PAVA candidate | 10 | 10 | 0.272990 | 0 |

All methods and all RB/WR heads have unstable bins. The instability is caused by sparse event bins and large observed-vs-predicted gaps in at least one bin per head. This blocks exact percentages and also blocks coarse-band release.

## 7. Monotonicity gate

Threshold contract:

`P(T6) <= P(T12) <= P(T24) <= P(T36) <= P(T48)`

| Split | Position | Method | Players checked | Adjacent violations | Max adjacent gap | Gate |
|---|---|---|---:|---:|---:|---|
| Validation | RB | Raw independent baseline | 106 | 18 | 0.072433 | blocked |
| Validation | RB | Post-hoc forward clamp benchmark | 106 | 0 | 0.000000 | pass |
| Validation | RB | Constrained/PAVA candidate | 106 | 0 | 0.000000 | pass |
| Validation | WR | Raw independent baseline | 154 | 80 | 0.009098 | blocked |
| Validation | WR | Post-hoc forward clamp benchmark | 154 | 0 | 0.000000 | pass |
| Validation | WR | Constrained/PAVA candidate | 154 | 0 | 0.000000 | pass |
| Test | RB | Raw independent baseline | 98 | 17 | 0.050787 | blocked |
| Test | RB | Post-hoc forward clamp benchmark | 98 | 0 | 0.000000 | pass |
| Test | RB | Constrained/PAVA candidate | 98 | 0 | 0.000000 | pass |
| Test | WR | Raw independent baseline | 163 | 79 | 0.011474 | blocked |
| Test | WR | Post-hoc forward clamp benchmark | 163 | 0 | 0.000000 | pass |
| Test | WR | Constrained/PAVA candidate | 163 | 0 | 0.000000 | pass |

Monotonicity passes for clamped and constrained holdout outputs. That remains necessary but not sufficient for release because calibration stability fails.

## 8. Coverage and sparse-head flags

| Target | Historical rows | Events | Train events | Validation events | Test events | Sparse flag | Recommendation |
|---|---:|---:|---:|---:|---:|---|---|
| `same_year_rb_t6` | 538 | 28 | 16 | 6 | 6 | yes | abstain or research-only |
| `same_year_rb_t12` | 538 | 54 | 33 | 10 | 11 | no | research candidate, not display-ready |
| `same_year_rb_t24` | 538 | 103 | 59 | 22 | 22 | no | research candidate, not display-ready |
| `same_year_rb_t36` | 538 | 159 | 92 | 33 | 34 | no | research candidate, not display-ready |
| `same_year_rb_t48` | 538 | 204 | 118 | 42 | 44 | no | research candidate, not display-ready |
| `same_year_wr_t6` | 817 | 26 | 16 | 5 | 5 | yes | abstain or research-only |
| `same_year_wr_t12` | 817 | 54 | 34 | 11 | 9 | no | research candidate, not display-ready |
| `same_year_wr_t24` | 817 | 106 | 64 | 21 | 21 | no | research candidate, not display-ready |
| `same_year_wr_t36` | 817 | 155 | 94 | 30 | 31 | no | research candidate, not display-ready |
| `same_year_wr_t48` | 817 | 209 | 127 | 40 | 42 | no | research candidate, not display-ready |

RB T6 and WR T6 remain abstain-or-research-only because of sparse support.

## 9. Forbidden feature scan

Forbidden feature scan result: pass.

5BI used 13 canonical prior-season features. All 13 passed the forbidden feature scan with `blocker=no`.

Confirmed absent from the 5BI feature list:

- ADP
- public rankings
- projections
- consensus
- market values
- trade values or calculators
- RotoWire rankings, projections, outlooks, or values
- prior fantasy draft history
- legacy `private_score`
- same-season final stats as preseason features
- label supplement sources as prediction features

## 10. Population policy result

Population policy result: pass.

| Gate | Status | Evidence |
|---|---|---|
| Waived/unscored players | pass | Historical holdout rows only; no current waived player scoring |
| Rookies | pass | `rookie_rows_scored=0` |
| Kickers | pass | `kicker_rows_scored=0` |
| Blocked current rows | pass | No blocked 2026 rows are scored by this holdout package |

Rookies remain excluded from veteran heads.

## 11. Artifact quarantine result

Artifact quarantine result: pass.

| Gate | Status | Evidence |
|---|---|---|
| Output folder scope | pass | `local_exports/outcome_probability/sprint_5bi_internal_holdout_calibration_package/` |
| App-readable probability table | pass | No app path is written; every row marks `app_readable=no` |
| Ranking/sorting output | pass | Every prediction row sets `sort_allowed=no` and `ranking_use_allowed=no` |
| Promoted model artifact | pass | No pickle, joblib, model package, app table, or promoted artifact is written |

No app loader/import path was changed. No Streamlit or app display file was changed.

## 12. Release-gate implications

Release recommendation: keep internal-only and blocked for release.

Blocked:

- Exact percentages remain blocked.
- Coarse bands remain blocked.
- App wiring remains blocked.
- Rankings/sorting remain blocked.
- Promoted model artifacts remain blocked.

Reason:

- Calibration-bin stability fails for every method and every RB/WR threshold head.
- Sparse-head abstention remains required for RB T6 and WR T6.
- Constrained monotonicity is promising but insufficient for release.

## 13. Required fixes, if any

No code fix is required to continue internal research.

Required before any future release discussion:

- Improve calibration-bin stability or define a stricter abstention/coarse-banding policy in a separate gated sprint.
- Re-run adversarial audit on the 5BI local-only package.
- Keep exact percentages blocked until calibration is stable.
- Keep app-readable outputs blocked unless HQ explicitly approves a release/display gate.

## 14. Next safe sprint recommendation

Recommended next sprint: `Sprint 5BJ - 5BI Holdout Package Adversarial Audit`

Scope:

- Audit the 5BI script and local-only outputs.
- Verify no app/import/ranking/sorting contamination.
- Confirm metric calculations and split discipline.
- Decide whether constrained/PAVA can continue as internal research or should move to calibration repair research.

## 15. Final gate label

Final gate label: `INTERNAL_HOLDOUT_CALIBRATION_RESEARCH_ONLY_BLOCKED_FOR_RELEASE`

Meaning:

- Adjusted validation/test prediction rows were generated.
- Raw vs clamped vs constrained Brier/log-loss comparison is now available.
- Constrained/PAVA clears monotonicity on validation/test.
- Calibration-bin stability fails across all RB/WR heads and methods.
- Exact percentages remain blocked.
- Coarse bands remain blocked.
- App wiring remains blocked.
- Rankings/sorting remain blocked.
- Promoted artifacts remain blocked.
