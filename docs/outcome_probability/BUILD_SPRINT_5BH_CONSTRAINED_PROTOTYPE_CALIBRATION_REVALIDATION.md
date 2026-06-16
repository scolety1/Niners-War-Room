# Sprint 5BH Constrained Prototype Calibration/Revalidation

## 1. Executive verdict

Verdict: `CONSTRAINED_PROTOTYPE_REVALIDATION_BLOCKED_BY_CALIBRATION`

Sprint 5BH revalidated the Sprint 5BF/5BG constrained/ordinal prototype after the adversarial audit. The constrained/PAVA candidate still removes all RB/WR adjacent-pair monotonicity violations and remains better behaved than the raw independent baseline and smaller-adjustment than the clamped benchmark.

The release gate remains blocked because the available artifacts do not contain adjusted validation/test holdout prediction rows for the clamped or constrained outputs. Raw 5AY Brier/log-loss metrics are available as reference only. They do not validate the adjusted clamped or constrained candidate.

Current release stance remains unchanged:

- Exact percentages remain blocked.
- App wiring remains blocked.
- Coarse-band display remains blocked.
- Rankings and sorting from outcome probabilities remain blocked.
- No app-readable probability or band table was created.
- No promoted model artifact was created.

## 2. Files/artifacts reviewed

Committed files reviewed:

- `docs/hq/PARALLEL_WORK_LANE_CONTRACT.md`
- `docs/hq/parallel_lanes/OUTCOME_COLUMN_CHAT_START.md`
- `docs/outcome_probability/BUILD_SPRINT_5BF_INTERNAL_CONSTRAINED_ORDINAL_PROTOTYPE.md`
- `docs/outcome_probability/BUILD_SPRINT_5BG_CONSTRAINED_ORDINAL_PROTOTYPE_ADVERSARIAL_AUDIT.md`
- `src/services/nwr_outcome_constrained_ordinal_prototype_service.py`
- `scripts/build_sprint_5bf_constrained_ordinal_internal_prototype.py`
- `tests/test_nwr_outcome_constrained_ordinal_prototype_service.py`

Local-only artifacts reviewed, not modified and not committed:

- `local_exports/outcome_probability/sprint_5ay_partial_threshold_model_evaluation/partial_2026_veteran_prediction_audit_internal_only.csv`
- `local_exports/outcome_probability/sprint_5ay_partial_threshold_model_evaluation/threshold_head_validation_metrics.csv`
- `local_exports/outcome_probability/sprint_5bf_constrained_ordinal_internal_prototype/prototype_comparison_summary.csv`
- `local_exports/outcome_probability/sprint_5bf_constrained_ordinal_internal_prototype/calibration_metrics_research_only.csv`
- `local_exports/outcome_probability/sprint_5bf_constrained_ordinal_internal_prototype/sparse_head_audit.csv`
- `local_exports/outcome_probability/sprint_5bf_constrained_ordinal_internal_prototype/coverage_audit.csv`
- `local_exports/outcome_probability/sprint_5bf_constrained_ordinal_internal_prototype/artifact_quarantine_audit.csv`

No new local-only exports were created in Sprint 5BH because this lane prompt treated `local_exports/` as forbidden for new work.

## 3. Artifact quarantine and path isolation

Quarantine result: pass for no app exposure; caution for stale path provenance.

The 5BF exporter writes only under `local_exports/outcome_probability/sprint_5bf_constrained_ordinal_internal_prototype/`, marks outputs `internal_only_not_app_readable`, sets app release status to `blocked_not_app_readable`, and writes no model object, app table, probability band table, ranking file, or promoted artifact.

Import/path isolation was reconfirmed:

- `nwr_outcome_constrained_ordinal_prototype_service` appears only in 5BF docs, the 5BF script, and the focused 5BF test.
- `sprint_5bf_constrained_ordinal_internal_prototype` appears only in outcome docs, the 5BF service/script/test path, and local-export references.
- `app/` scan found no constrained-ordinal service, export folder, or constrained-ordinal import references.

One artifact caution: the existing `artifact_quarantine_audit.csv` evidence path names `C:/Users/smcol/Documents/Vacation/Niners-War-Room/local_exports/...` rather than the active outcome worktree `C:/Users/smcol/Documents/Vacation/Niners-War-Room-outcome/...`. This does not create an app-readable artifact, but it means 5BF local-export provenance should be refreshed if HQ authorizes a future 5BH export package.

## 4. Raw vs clamped vs constrained metric comparison

Monotonicity and adjustment comparison was recomputed in memory from the 5AY internal prediction audit. No files were written.

| Position | Players reviewed | Raw violations | Raw affected players | Raw max gap | Clamped violations | Clamped adjusted cells | Clamped max abs delta | Clamped avg abs delta | Constrained violations | Constrained adjusted cells | Constrained max abs delta | Constrained avg abs delta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| RB | 125 | 3 | 3 | 0.012790 | 0 | 3 | 0.012790 | 0.007663 | 0 | 6 | 0.006395 | 0.003831 |
| WR | 201 | 27 | 15 | 0.002894 | 0 | 29 | 0.005119 | 0.001751 | 0 | 43 | 0.002671 | 0.000787 |

Raw 5AY metric references:

| Target | Raw validation Brier | Raw test Brier | Raw validation log loss | Raw test log loss | Raw bin status | Clamped metric status | Constrained metric status |
|---|---:|---:|---:|---:|---|---|---|
| `same_year_rb_t6` | 0.046973 | 0.052075 | 0.185922 | 0.185615 | unstable bins present | not validated | not validated |
| `same_year_rb_t12` | 0.080124 | 0.080881 | 0.282392 | 0.263180 | unstable bins present | not validated | not validated |
| `same_year_rb_t24` | 0.147856 | 0.122885 | 0.455809 | 0.393314 | unstable bins present | not validated | not validated |
| `same_year_rb_t36` | 0.155485 | 0.154269 | 0.478255 | 0.481675 | unstable bins present | not validated | not validated |
| `same_year_rb_t48` | 0.170237 | 0.166076 | 0.517101 | 0.513530 | unstable bins present | not validated | not validated |
| `same_year_wr_t6` | 0.027448 | 0.027990 | 0.108805 | 0.115150 | unstable bins present | not validated | not validated |
| `same_year_wr_t12` | 0.054601 | 0.043720 | 0.192542 | 0.161524 | unstable bins present | not validated | not validated |
| `same_year_wr_t24` | 0.073445 | 0.076342 | 0.244732 | 0.248740 | unstable bins present | not validated | not validated |
| `same_year_wr_t36` | 0.080609 | 0.096814 | 0.273706 | 0.312870 | unstable bins present | not validated | not validated |
| `same_year_wr_t48` | 0.089855 | 0.111248 | 0.307736 | 0.354593 | unstable bins present | not validated | not validated |

Finding: raw Brier/log-loss metrics exist, but clamped and constrained Brier/log-loss cannot be claimed from the current artifacts. The adjusted outputs need fresh validation/test prediction rows before any calibration comparison can pass.

## 5. Calibration-bin stability

Calibration-bin result: blocked.

All RB/WR raw threshold heads reviewed in 5BF are marked `unstable_bins_present`. The sparse-bin risk is especially important because the constrained/PAVA candidate changes probabilities after raw model scoring. Even small adjustments can alter bin membership, observed-vs-expected calibration, and log-loss behavior.

Because 5BF local artifacts do not include adjusted validation/test holdout predictions, 5BH cannot confirm that clamped or constrained calibration bins are stable.

## 6. Monotonicity gate

Monotonicity result: pass for internal constrained candidate only.

The 5BB top-N-or-better contract remains:

`P(T6) <= P(T12) <= P(T24) <= P(T36) <= P(T48)`

Recomputed results:

- Raw independent baseline: 30 RB/WR adjacent-pair violations.
- Post-hoc clamped benchmark: 0 adjacent-pair violations.
- Constrained/PAVA candidate: 0 adjacent-pair violations.

This is necessary evidence for continuing internal research. It is not sufficient evidence for release.

## 7. Coverage and sparse-head findings

Coverage findings from the 5BF local audit:

| Coverage item | Count | Status | Prototype policy |
|---|---:|---|---|
| Ready 2026 veteran feature rows | 520 | scored internal-only | eligible for internal research only |
| Blocked 2026 veteran feature rows | 172 | not scored | do not score without valid features |
| Top-priority waived players missing features | 5 | not scored waived for partial training | do not score without valid features |
| Rookie rows | 80 | excluded separate path | exclude from veteran heads |
| Kicker rows | 8 | not applicable | not applicable |
| App probability files created | 0 | none | audit only no release permission |
| Promoted model artifacts created | 0 | none | audit only no release permission |

Sparse-head findings:

| Target | Historical rows | Events | Validation events | Test events | Sparse flag | Abstention requirement |
|---|---:|---:|---:|---:|---|---|
| `same_year_rb_t6` | 538 | 28 | 6 | 6 | yes | abstain or research-only |
| `same_year_wr_t6` | 817 | 26 | 5 | 5 | yes | abstain or research-only |

All other RB/WR heads remain research candidates only and are not display-ready.

## 8. Population policy gate

Population policy result: pass for current internal audit evidence.

- No waived/unscored players were scored according to the coverage audit.
- Rookies are excluded from veteran heads and remain a separate path.
- Kickers are not scored.
- The constrained prototype comparison processes RB/WR threshold chains only.
- QB/TE current prediction rows exist in the broader 5AY prediction audit, but they are not part of the constrained RB/WR chain revalidation.

## 9. Release-gate implications

Release result: blocked.

The constrained/PAVA candidate can continue as internal research, but it cannot release exact percentages, coarse bands, app wiring, rankings, sorting, or promoted artifacts.

The current blocker is calibration, not monotonicity. A release candidate would need fresh validation/test adjusted predictions and metrics for raw, clamped, and constrained methods on the same splits, plus refreshed calibration-bin stability checks and artifact quarantine evidence.

## 10. Required fixes, if any

Required before any future probability release:

- Produce a fresh internal-only 5BH validation package, if HQ authorizes local exports, with adjusted clamped and constrained validation/test prediction rows.
- Calculate Brier and log-loss for raw, clamped, and constrained outputs on the same validation/test splits.
- Rebuild calibration-bin audits for clamped and constrained outputs, not only raw.
- Refresh artifact quarantine evidence so recorded paths match the active worktree.
- Keep all outputs under a sprint-specific internal-only local-export folder with `internal_only_not_app_readable` or `blocked_not_app_readable` labels.
- Continue abstention for sparse heads, especially RB T6 and WR T6.

No code fix was required in the committed 5BF service for this docs-only revalidation.

## 11. Next safe sprint recommendation

Recommended next sprint: `Sprint 5BI - Authorized Internal Holdout Calibration Package`

Scope:

- Internal-only, no app output.
- Generate validation/test adjusted prediction rows for raw, clamped, and constrained methods.
- Compute Brier/log-loss and calibration-bin stability on identical splits.
- Refresh quarantine metadata in the active outcome worktree.
- Keep exact percentages, coarse bands, app wiring, rankings, sorting, and promoted artifacts blocked.

## 12. Final gate label

Final gate label: `CONSTRAINED_PROTOTYPE_REVALIDATION_BLOCKED_BY_CALIBRATION`

Meaning:

- Constrained/PAVA monotonicity still passes internally.
- Raw independent baseline remains blocked.
- Clamped benchmark remains benchmark-only.
- Adjusted clamped/constrained calibration is not established.
- Exact percentages remain blocked.
- App wiring remains blocked.
- Coarse-band display remains blocked.
- Rankings/sorting remain blocked.
- No app-readable output was created.
- No promoted artifact was created.
