# Sprint 5BG Constrained/Ordinal Prototype Adversarial Audit

## 1. Executive Verdict

Verdict: `CONSTRAINED_ORDINAL_PROTOTYPE_AUDIT_PASS_INTERNAL_ONLY`

Sprint 5BG adversarially audited the committed Sprint 5BF prototype at `f4f0cce`.

The audit found no 5BF-specific blocker from artifact risk, leakage risk, app-import risk, ranking/sorting contamination, release overclaim, population-policy violation, or focused test failure. The prototype remains internal-only and earns only a follow-up calibration/revalidation sprint. It does not release probabilities.

The broad `pytest tests -k "outcome"` suite remains yellow because of existing `model_v4` local-export dependency failures. Those failures are not 5BF blockers, but they should stay documented so they are not confused with the constrained/ordinal prototype.

Current release stance:

- Exact percentages remain blocked.
- App wiring remains blocked.
- Coarse-band display remains blocked.
- Rankings and sorting remain blocked.
- No promoted model artifact exists.
- No head is app-ready.

## 2. Files And Artifacts Reviewed

Committed 5BF files reviewed:

- `src/services/nwr_outcome_constrained_ordinal_prototype_service.py`
- `scripts/build_sprint_5bf_constrained_ordinal_internal_prototype.py`
- `tests/test_nwr_outcome_constrained_ordinal_prototype_service.py`
- `docs/outcome_probability/BUILD_SPRINT_5BF_INTERNAL_CONSTRAINED_ORDINAL_PROTOTYPE.md`

Local-only artifacts reviewed:

`local_exports/outcome_probability/sprint_5bf_constrained_ordinal_internal_prototype/`

Key local-only files reviewed:

- `metadata_sprint_5bf.json`
- `artifact_quarantine_audit.csv`
- `release_gate_blockers.csv`
- `forbidden_feature_scan.csv`
- `prototype_comparison_summary.csv`
- `coverage_audit.csv`
- `threshold_release_recommendation_audit.csv`
- `calibration_metrics_research_only.csv`

Local exports were inspected but not committed.

## 3. Git And Commit Baseline

Commands run:

- `git status --short`
- `git log --oneline -8`
- `git show --stat f4f0cce`
- `git diff --check`

Baseline findings:

- Current branch head at audit start: `f4f0cce Prototype internal constrained ordinal threshold repair`.
- `git status --short` showed only `?? data/`.
- `data/` remains untracked and uncommitted.
- `git diff --check` was clean.

Commit `f4f0cce` changed only the expected 5BF files:

- `docs/outcome_probability/BUILD_SPRINT_5BF_INTERNAL_CONSTRAINED_ORDINAL_PROTOTYPE.md`
- `scripts/build_sprint_5bf_constrained_ordinal_internal_prototype.py`
- `src/services/nwr_outcome_constrained_ordinal_prototype_service.py`
- `tests/test_nwr_outcome_constrained_ordinal_prototype_service.py`

No `data/`, `local_exports/`, recovery zip, cache, app file, ranking file, or unrelated file was committed in `f4f0cce`.

## 4. Artifact Quarantine Findings

Result: pass.

Local artifact metadata:

- `output_scope`: `internal_only_not_app_readable`
- `app_release_status`: `blocked_not_app_readable`
- `exact_percentages`: `blocked`
- `app_wiring`: `blocked`
- `coarse_bands`: `blocked_until_separate_gate`
- `model_artifact_promoted`: `false`
- `app_readable_output_created`: `false`
- `ranking_sorting_changed`: `false`

Artifact quarantine audit:

| Gate | Status | Evidence | Release impact |
|---|---|---|---|
| Output folder scope | pass | Outputs are under `local_exports/outcome_probability/sprint_5bf_constrained_ordinal_internal_prototype/` | blocked not app-readable |
| App-readable output path | pass | No app or app-data path is written by exporter | app wiring blocked |
| Ranking/sorting output | pass | Row-level outputs set `sort_allowed=no` and `ranking_use_allowed=no` | rankings/sorting blocked |
| Promoted model artifact | pass | No model object, pickle, package, or promoted artifact is written | artifact promotion blocked |

No probability or band table is placed in an app-loaded path.

## 5. Import And Path Isolation Findings

Result: pass.

Required greps run:

- `git grep -n "nwr_outcome_constrained_ordinal_prototype_service" -- .`
- `git grep -n "constrained_ordinal" -- app src scripts tests docs`
- `git grep -n "sprint_5bf_constrained_ordinal_internal_prototype" -- .`
- Additional app-only scan: `rg -n "nwr_outcome_constrained_ordinal_prototype_service|constrained_ordinal|sprint_5bf_constrained_ordinal_internal_prototype" app -S`

Findings:

- Prototype service import appears only in the 5BF script and 5BF test.
- Documentation references appear in 5BE/5BF docs.
- The service contains its own quarantine folder constants and metadata strings.
- `app/` scan returned no matches.

No blocked references were found in:

- Streamlit app pages/components
- player detail card code
- rankings/sorting code
- release/display services
- app loaders
- sort/rank/value pipelines

No app/runtime/display/ranking path imports or consumes the prototype service or 5BF local exports.

## 6. Leakage And Schema Findings

Result: pass.

`forbidden_feature_scan.csv` status:

- 14 feature rows checked.
- 14 passed.
- 0 forbidden feature failures.

No evidence was found that 5BF used forbidden prediction features:

- ADP
- public rankings
- projections
- consensus
- market values
- trade calculators
- prior fantasy draft history
- RotoWire rankings/projections/outlooks/values
- legacy `private_score`
- same-season final stats as preseason features
- label supplement sources as prediction features

5BF uses existing 5AY internal-only prediction rows and associated legal feature scan artifacts for the constrained projection audit. It does not introduce a new feature source or fit a release model.

## 7. Monotonicity Findings

Result: pass for internal constrained candidate; raw baseline remains blocked.

5BB semantics confirmed:

`P(T6) <= P(T12) <= P(T24) <= P(T36) <= P(T48)` for RB/WR.

5BF local metadata:

- Raw violation count: 30
- Clamped violation count: 0
- Constrained violation count: 0

Prototype comparison:

| Position | Players reviewed | Raw violations | Raw affected players | Raw max gap | Clamped violations | Constrained violations |
|---|---:|---:|---:|---:|---:|---:|
| RB | 125 | 3 | 3 | 0.012790 | 0 | 0 |
| WR | 201 | 27 | 15 | 0.002894 | 0 | 0 |

Findings:

- Raw independent baseline remains blocked.
- Post-hoc clamped benchmark remains benchmark-only.
- Constrained isotonic/PAVA candidate has zero adjacent-pair violations.
- Monotonicity success is necessary but not sufficient for release.

## 8. Calibration And Release-Claim Findings

Result: pass with release still blocked.

5BF does not call adjusted outputs calibrated release probabilities. Metadata and metric exports state:

- `calibration_status`: `research_only_prior_metrics_not_valid_for_adjusted_outputs`
- Clamped calibration status: `requires_fresh_validation`
- Constrained calibration status: `requires_fresh_validation`

Release claims audited:

- Exact percentages remain blocked.
- Coarse bands remain blocked from app display.
- No head is declared app-ready.
- No calibrated probability artifact was promoted.
- Successful prototype earns only follow-up adversarial audit and future calibration/revalidation work.

No release overclaim was found.

## 9. Population Policy Findings

Result: pass.

Coverage audit:

| Coverage item | Count | Source status | Prototype policy |
|---|---:|---|---|
| Ready 2026 veteran feature rows | 520 | scored internal-only | eligible for internal research only |
| Blocked 2026 veteran feature rows | 172 | not scored | do not score without valid features |
| Top-priority waived players missing features | 5 | not scored waived for partial training | do not score without valid features |
| Rookie rows | 80 | excluded separate path | exclude from veteran heads |
| Kicker rows | 8 | not applicable | not applicable |

Findings:

- Waived/unscored players are not scored.
- Rookies are not forced through veteran heads.
- Kickers are not scored.
- Blocked rows remain blocked.

## 10. Ranking And Sorting Contamination Findings

Result: pass.

Findings:

- No probability output changes rankings.
- No hidden probability sort key exists in app/ranking paths.
- No app ranking service consumes 5BF output.
- Row-level 5BF outputs include `sort_allowed=no` and `ranking_use_allowed=no`.
- Greps found no app, rankings, display, or value-pipeline import of the prototype.

Rankings and sorting remain blocked.

## 11. Test-Status Findings

Focused 5BF checks:

- `python -m pytest tests/test_nwr_outcome_constrained_ordinal_prototype_service.py -q`
  - Result: 4 passed.
- `ruff check src/services/nwr_outcome_constrained_ordinal_prototype_service.py scripts/build_sprint_5bf_constrained_ordinal_internal_prototype.py tests/test_nwr_outcome_constrained_ordinal_prototype_service.py`
  - Result: passed.
- `python -m py_compile src/services/nwr_outcome_constrained_ordinal_prototype_service.py scripts/build_sprint_5bf_constrained_ordinal_internal_prototype.py`
  - Result: passed.
- `git diff --check`
  - Result: clean.

Broad outcome-keyword check:

- `python -m pytest tests -k "outcome" -q`
  - Result: 136 passed, 6 failed, 1509 deselected.

Failed broad outcome tests:

- `tests/test_model_v4_historical_similarity_service.py::test_historical_similarity_missing_outcomes_are_unknown_not_misses`
- `tests/test_model_v4_rookie_outcome_label_service.py::test_rookie_outcome_labels_use_rotowire_stats_without_changing_scores`
- `tests/test_model_v4_rookie_outcome_label_service.py::test_rookie_outcome_label_writer_exports_expected_files`
- `tests/test_model_v4_rookie_outcome_label_service.py::test_historical_tuning_report_uses_full_outcome_labels`
- `tests/test_model_v4_rookie_outcome_label_service.py::test_historical_tuning_summary_separates_universe_and_hit_strictness`
- `tests/test_model_v4_startup_slot_simulator_service.py::test_outcome_buckets_are_context_only_and_honest_about_samples`

Classification:

- Yellow, not a 5BF blocker.
- Failures are in existing `model_v4` outcome tests, not the 5BF constrained/ordinal prototype tests.
- Four failures are direct `FileNotFoundError` cases for missing `local_exports/model_v4/evidence_matrices/latest/historical_rookie_backtest_feature_matrix.csv`.
- The historical similarity and startup slot failures are also outside the 5BF prototype path and match existing local-export dependency/context issues.
- No 5BF service, script, report, or test failure was found.

No unrelated tests were patched.

## 12. Required Fixes, If Any

No 5BF-specific fixes are required before continuing internal research.

Recommended follow-up outside 5BF:

- Classify or restore the missing `model_v4` local exports used by the broad outcome-keyword tests.
- Keep those failures separate from NWR Outcome Probability constrained prototype audit results.

## 13. Final Release Stance

Release stance: internal-only pass.

Allowed next step:

- Fresh internal calibration/revalidation of the constrained prototype.

Still blocked:

- exact percentages
- app wiring
- app-readable probability tables
- app-readable band tables
- player-facing percentages
- player-facing bands
- rankings/sorting changes
- decision automation
- promoted model artifacts
- fake/placeholder probabilities

## 14. Final Gate Label

Final gate label: `CONSTRAINED_ORDINAL_PROTOTYPE_AUDIT_PASS_INTERNAL_ONLY`

Meaning:

- No artifact, leakage, app-import, ranking/sorting, release-overclaim, or 5BF-specific test risk was found.
- The constrained prototype remains internal-only.
- A successful audit does not release probabilities.
- Exact percentages remain blocked.
- App wiring remains blocked.
- Coarse-band display remains blocked.
- No head is app-ready.
