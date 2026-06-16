# Sprint 5BF Internal Constrained/Ordinal Prototype

## 1. Executive Verdict

Verdict: `CONSTRAINED_ORDINAL_PROTOTYPE_INTERNAL_ONLY_CONTINUE`

Output scope: `internal_only_not_app_readable`

Sprint 5BF implemented an internal-only constrained threshold prototype for RB/WR same-year threshold heads. The prototype compares:

- raw independent 5AY-style heads
- post-hoc forward clamping benchmark
- constrained isotonic/PAVA projection

The constrained isotonic/PAVA projection removes RB/WR adjacent-threshold monotonicity violations and uses smaller maximum/average adjustments than forward clamping. This is useful research evidence, but it does not release probabilities. Adjusted outputs require fresh calibration validation, a follow-up adversarial audit, and all release gates before any app or display use.

Current release state:

- Exact percentages remain blocked.
- App wiring remains blocked.
- Coarse-band display remains blocked.
- Rankings and sorting remain blocked.
- No promoted model artifact was created.
- No head is app-ready.

## 2. Files, Code, And Artifacts Changed

Code/test files created:

- `src/services/nwr_outcome_constrained_ordinal_prototype_service.py`
- `scripts/build_sprint_5bf_constrained_ordinal_internal_prototype.py`
- `tests/test_nwr_outcome_constrained_ordinal_prototype_service.py`

Report created:

- `docs/outcome_probability/BUILD_SPRINT_5BF_INTERNAL_CONSTRAINED_ORDINAL_PROTOTYPE.md`

Local-only exports created under:

`local_exports/outcome_probability/sprint_5bf_constrained_ordinal_internal_prototype/`

Export files:

- `artifact_quarantine_audit.csv`
- `calibration_metrics_research_only.csv`
- `constrained_isotonic_adjustments_internal_only.csv`
- `constrained_isotonic_prototype_violations.csv`
- `coverage_audit.csv`
- `feature_schema_audit.csv`
- `forbidden_feature_scan.csv`
- `metadata_sprint_5bf.json`
- `posthoc_clamped_benchmark_adjustments_internal_only.csv`
- `posthoc_clamped_benchmark_violations.csv`
- `prototype_comparison_summary.csv`
- `raw_independent_baseline_violations.csv`
- `README_SPRINT_5BF.md`
- `release_gate_blockers.csv`
- `sparse_head_audit.csv`
- `split_discipline_audit.csv`
- `threshold_release_recommendation_audit.csv`
- `threshold_semantics_audit.csv`

These exports are research-only, ignored/uncommitted, and not app-readable.

## 3. Safety And Artifact Quarantine Check

| Gate | Result | Evidence | Release impact |
|---|---|---|---|
| Legal feature schema only | pass | Forbidden feature failures: 0 | Leakage gate still required for any future release |
| Constrained monotonicity | pass | Constrained violations: 0 | Necessary but not sufficient |
| No app-readable output path | pass | Outputs written only under `local_exports/outcome_probability/sprint_5bf_constrained_ordinal_internal_prototype/` | App wiring blocked |
| No ranking/sorting output | pass | Row-level outputs use `sort_allowed=no` and `ranking_use_allowed=no` | Rankings/sorting blocked |
| No promoted artifacts | pass | Only CSV/JSON/README research exports written | Artifact promotion blocked |
| Blocked/waived/rookie/kicker policy | pass | Blocked rows not scored: 172; rookies excluded: 80; kickers not applicable: 8 | Coverage gate still required |
| Calibration metrics research-only | pass | Raw 5AY metrics exported; adjusted outputs require fresh validation | Exact percentages blocked |

No Streamlit/app code changed. No player detail card, rankings, sorting, or app data surface was modified.

## 4. Prototype Implementation Summary

Implemented service:

`src/services/nwr_outcome_constrained_ordinal_prototype_service.py`

Implemented runner:

`scripts/build_sprint_5bf_constrained_ordinal_internal_prototype.py`

Implemented focused tests:

`tests/test_nwr_outcome_constrained_ordinal_prototype_service.py`

Prototype methods:

1. Raw independent baseline
   - Loads 5AY internal-only RB/WR prediction rows.
   - Audits 5BB threshold direction.
   - Retains known RB/WR violations.

2. Post-hoc forward clamping benchmark
   - Applies `T12 = max(T12, T6)`, `T24 = max(T24, T12)`, `T36 = max(T36, T24)`, `T48 = max(T48, T36)`.
   - Removes violations.
   - Remains benchmark-only and not release-ready.

3. Constrained isotonic/PAVA projection
   - Applies a nondecreasing isotonic projection over each player's threshold chain.
   - Minimizes squared adjustment to the raw chain while enforcing monotonicity.
   - Serves as the Sprint 5BF constrained/ordinal fallback prototype.

Deferred:

- Full trained cumulative/ordinal model.
- Shared constrained-threshold model with learned threshold intercepts.
- Calibration refit for adjusted outputs.

Those are larger training tasks and should be handled only after this prototype passes adversarial audit.

## 5. Raw Baseline Results

Required RB/WR chain:

`P(T6) <= P(T12) <= P(T24) <= P(T36) <= P(T48)`

| Position | Players reviewed | Raw violations | Affected players | Max violation gap | Release stance |
|---|---:|---:|---:|---:|---|
| RB | 125 | 3 | 3 | 0.012790 | blocked |
| WR | 201 | 27 | 15 | 0.002894 | blocked |

Raw independent heads reproduce the prior 5BA/5BC issue:

- RB violations: `T36 > T48`.
- WR violations: `T6 > T12` and `T12 > T24`.

Raw independent heads remain blocked from app use.

## 6. Clamped Benchmark Results

| Position | Violations after clamp | Affected players | Adjusted cells | Max abs delta | Average abs delta | Calibration status |
|---|---:|---:|---:|---:|---:|---|
| RB | 0 | 3 | 3 | 0.012790 | 0.007663 | requires fresh validation |
| WR | 0 | 15 | 29 | 0.005119 | 0.001751 | requires fresh validation |

Clamping removes monotonicity violations, but it changes outputs. Prior 5AY calibration metrics do not apply to the clamped values.

Clamping remains internal benchmark only.

## 7. Constrained/Ordinal Prototype Results

Implemented constrained candidate: `constrained_isotonic_pava_projection`.

| Position | Violations after constrained projection | Affected players | Adjusted cells | Max abs delta | Average abs delta | Calibration status |
|---|---:|---:|---:|---:|---:|---|
| RB | 0 | 3 | 6 | 0.006395 | 0.003831 | requires fresh validation |
| WR | 0 | 15 | 43 | 0.002671 | 0.000787 | requires fresh validation |

Interpretation:

- The constrained projection removes all RB/WR adjacent-pair violations.
- It makes smaller maximum and average adjustments than forward clamping.
- It adjusts both sides of a violation when needed, instead of only raising broader thresholds.
- It is more attractive than clamping as an internal repair candidate.
- It still does not solve calibration or release readiness.

## 8. Calibration And Metric Comparison

Raw 5AY metrics were carried forward as research-only reference metrics. Adjusted clamped and constrained outputs require fresh validation.

| Target | Raw validation Brier | Raw test Brier | Raw calibration status | Clamped status | Constrained status |
|---|---:|---:|---|---|---|
| `same_year_rb_t6` | 0.046973 | 0.052075 | unstable bins present | requires fresh validation | requires fresh validation |
| `same_year_rb_t12` | 0.080124 | 0.080881 | unstable bins present | requires fresh validation | requires fresh validation |
| `same_year_rb_t24` | 0.147856 | 0.122885 | unstable bins present | requires fresh validation | requires fresh validation |
| `same_year_rb_t36` | 0.155485 | 0.154269 | unstable bins present | requires fresh validation | requires fresh validation |
| `same_year_rb_t48` | 0.170237 | 0.166076 | unstable bins present | requires fresh validation | requires fresh validation |
| `same_year_wr_t6` | 0.027448 | 0.027990 | unstable bins present | requires fresh validation | requires fresh validation |
| `same_year_wr_t12` | 0.054601 | 0.043720 | unstable bins present | requires fresh validation | requires fresh validation |
| `same_year_wr_t24` | 0.073445 | 0.076342 | unstable bins present | requires fresh validation | requires fresh validation |
| `same_year_wr_t36` | 0.080609 | 0.096814 | unstable bins present | requires fresh validation | requires fresh validation |
| `same_year_wr_t48` | 0.089855 | 0.111248 | unstable bins present | requires fresh validation | requires fresh validation |

Calibration finding:

- Raw calibration remains unstable.
- Clamped calibration is not established.
- Constrained calibration is not established.
- Exact percentages remain blocked.

## 9. Coverage And Sparse-Head Findings

Coverage carried forward from 5AY:

- Ready 2026 veteran feature rows: 520.
- Blocked 2026 veteran feature rows: 172.
- Top-priority waived players missing features: 5.
- Rookie rows excluded: 80.
- Kicker rows not applicable: 8.

RB/WR support:

| Target | Historical rows | Events | Train events | Validation events | Test events | Sparse flag |
|---|---:|---:|---:|---:|---:|---|
| `same_year_rb_t6` | 538 | 28 | 16 | 6 | 6 | yes |
| `same_year_rb_t12` | 538 | 54 | 33 | 10 | 11 | no |
| `same_year_rb_t24` | 538 | 103 | 59 | 22 | 22 | no |
| `same_year_rb_t36` | 538 | 159 | 92 | 33 | 34 | no |
| `same_year_rb_t48` | 538 | 204 | 118 | 42 | 44 | no |
| `same_year_wr_t6` | 817 | 26 | 16 | 5 | 5 | yes |
| `same_year_wr_t12` | 817 | 54 | 34 | 11 | 9 | no |
| `same_year_wr_t24` | 817 | 106 | 64 | 21 | 21 | no |
| `same_year_wr_t36` | 817 | 155 | 94 | 30 | 31 | no |
| `same_year_wr_t48` | 817 | 209 | 127 | 40 | 42 | no |

Abstention recommendations:

- RB T6 and WR T6 should remain abstain-or-research-only due to sparse support.
- All heads remain internal-only until calibration, coverage, and release gates pass.

## 10. Gate Results

| Gate | Result | Notes |
|---|---|---|
| Legal feature schema only | pass | 5AY forbidden feature scan reused; 0 failures |
| Forbidden feature scan | pass | No blocked feature names in scan |
| Split discipline | pass | Uses 5AY split metrics; no current rows fit parameters |
| Threshold semantics | pass | RB/WR top-N-or-better chain audited |
| Monotonicity direction | pass for constrained candidate | 0 constrained violations |
| No app-readable output path | pass | Outputs only in 5BF `local_exports` folder |
| No ranking/sorting output | pass | `sort_allowed=no`, `ranking_use_allowed=no` |
| No promoted artifacts | pass | No model object/package written |
| No waived/unscored players scored | pass | Blocked/waived rows remain unscored |
| Rookies excluded from veteran heads | pass | Rookies remain excluded |
| Kickers not applicable | pass | Kickers remain not applicable |
| Calibration metrics research-only | pass | Adjusted outputs require fresh validation |
| Baseline comparison | pass | Raw, clamped, and constrained compared |

## 11. Release Recommendation

Recommendation: `INTERNAL_ONLY_FOLLOWUP_ADVERSARIAL_AUDIT`

The constrained prototype should continue as internal research because it resolves monotonicity with smaller adjustment than clamping and no app/artifact/ranking contamination was found.

It does not release probabilities. It does not permit app wiring. It does not permit exact percentages. It does not permit coarse-band display.

## 12. Next Safe Sprint Recommendation

Recommended next sprint: `Sprint 5BG - Constrained Prototype Adversarial Audit`

5BG should adversarially audit:

- constrained/PAVA implementation correctness
- split discipline
- calibration invalidation and future validation plan
- sparse-head abstention policy
- local export quarantine
- app-output absence
- ranking/sorting absence
- blocked/waived/rookie/kicker policy

Only after 5BG should a future sprint consider a trained cumulative/ordinal or shared constrained model with fresh holdout calibration.

## 13. Final Gate Label

Final gate label: `CONSTRAINED_ORDINAL_PROTOTYPE_INTERNAL_ONLY_CONTINUE`

Meaning:

- Internal constrained prototype can continue to adversarial audit.
- Exact percentages remain blocked.
- App wiring remains blocked.
- Coarse bands remain blocked until a separate coarse-band gate passes.
- No app-readable probability or band output was created.
- No rankings/sorting changes were made.
- No model artifact was promoted.
- No head is app-ready.
