# Sprint 5BC Internal Monotonic Repair Prototype Comparison

## 1. Executive Verdict

Verdict: `MONOTONIC_REPAIR_PROTOTYPE_INTERNAL_ONLY_CONTINUE`

Sprint 5BC compared internal-only monotonic repair options for RB and WR same-year threshold heads under the Sprint 5BB threshold semantics contract.

The post-hoc clamping benchmark successfully removes the known RB/WR monotonicity violations, but it changes model outputs and therefore invalidates the prior calibration claims for the repaired values. It is useful as an internal benchmark only. It is not release-ready, not app-readable, not player-facing, and not suitable for rankings or sorting.

Current release state:

- Exact percentages remain blocked.
- App wiring remains blocked.
- Rankings and sorting remain blocked.
- Player-facing bands remain blocked.
- Coarse-band research may continue only as quarantined internal research.
- No promoted model artifact was created.

## 2. Inputs And Artifacts Reviewed

Reviewed:

- `docs/outcome_probability/BUILD_SPRINT_5BB_THRESHOLD_SEMANTICS_MONOTONICITY_CONTRACT.md`
- `local_exports/outcome_probability/sprint_5ay_partial_threshold_model_evaluation/partial_2026_veteran_prediction_audit_internal_only.csv`
- `local_exports/outcome_probability/sprint_5ay_partial_threshold_model_evaluation/threshold_head_support.csv`
- `local_exports/outcome_probability/sprint_5ay_partial_threshold_model_evaluation/threshold_head_validation_metrics.csv`
- `local_exports/outcome_probability/sprint_5ay_partial_threshold_model_evaluation/threshold_release_decision_table.csv`
- `local_exports/outcome_probability/sprint_5ay_partial_threshold_model_evaluation/coverage_warning_audit.csv`
- `local_exports/outcome_probability/sprint_5ay_partial_threshold_model_evaluation/forbidden_feature_scan.csv`

Created local-only exports under:

`local_exports/outcome_probability/sprint_5bc_internal_monotonic_repair_prototype_comparison/`

Created:

- `raw_independent_monotonicity_baseline_inventory.csv`
- `posthoc_clamping_adjustment_inventory_internal_only.csv`
- `posthoc_clamping_post_repair_violations.csv`
- `monotonic_repair_comparison_summary.csv`
- `repair_approach_release_risk_matrix.csv`
- `coarse_band_research_feasibility_aggregate_only.csv`
- `coarse_band_shift_audit_aggregate_only.csv`
- `artifact_quarantine_and_safety_audit.csv`
- `metadata_sprint_5bc.json`
- `README_SPRINT_5BC.md`

These exports are internal-only research artifacts. They are not app-readable, not committed, and not release artifacts.

## 3. Safety And Artifact Quarantine Check

Result: pass.

| Risk area | Result | Evidence |
|---|---|---|
| Local-only export scope | pass | 5BC outputs are written only under `local_exports/outcome_probability/sprint_5bc_internal_monotonic_repair_prototype_comparison/`. |
| App probability table creation | pass | No app path or source path was written; generated rows carry blocked/not-app-readable flags. |
| Forbidden feature leakage | pass | 5AY forbidden-feature scan failures: 0 across 14 feature names. |
| Waived/unscored players | pass | 5BC reuses only ready RB/WR rows already present in the 5AY internal prediction export. |
| Rookie or kicker forced scoring | pass | 5BC evaluates only RB/WR veteran threshold rows. |
| Ranking/sorting contamination | pass | Generated rows mark `sort_allowed=no` and `ranking_use_allowed=no`; app code and rankings files were not modified. |
| Promoted model artifact | pass | No model object was saved or promoted. |

No waived players were scored. No blocked rows were scored. Rookies remain excluded from veteran heads. Kickers remain not applicable.

## 4. Raw Independent Baseline Results

The raw independent heads retain the RB/WR monotonicity failures from Sprints 5BA and 5BB.

Required RB/WR contract:

`P(T6) <= P(T12) <= P(T24) <= P(T36) <= P(T48)`

| Position | Players reviewed | Raw violating adjacent pairs | Raw affected players | Violating pair counts | Max gap | Average gap | Release recommendation |
|---|---:|---:|---:|---|---:|---:|---|
| RB | 125 | 3 | 3 | `T36>T48:3` | 0.012790 | 0.007663 | blocked from app use |
| WR | 201 | 27 | 15 | `T12>T24:15`; `T6>T12:12` | 0.002894 | 0.001221 | blocked from app use |

Interpretation:

- RB violations are localized to `T36 > T48`.
- WR violations are small in magnitude but more frequent, clustered at `T6 > T12` and `T12 > T24`.
- Raw independent heads remain blocked because independent one-vs-threshold outputs do not guarantee threshold ordering.

## 5. Post-Hoc Clamping Benchmark Results

Benchmark rule applied internally:

- `T12 = max(T12, T6)`
- `T24 = max(T24, T12)`
- `T36 = max(T36, T24)`
- `T48 = max(T48, T36)`

This benchmark enforces nondecreasing probabilities from narrow to wide thresholds for each player.

| Position | Pre-clamp violating pairs | Post-clamp violating pairs | Affected players | Adjusted cells | Max repair delta | Average repair delta | Calibration effect |
|---|---:|---:|---:|---:|---:|---:|---|
| RB | 3 | 0 | 3 | 3 | 0.012790 | 0.007663 | prior calibration invalid for repaired output |
| WR | 27 | 0 | 15 | 29 | 0.005119 | 0.001751 | prior calibration invalid for repaired output |

Clarifying note: the raw max gap measures one adjacent threshold inversion, while repair delta can be larger when clamping cascades across multiple thresholds for the same player. This does not make the repaired output release-ready because repaired values still require fresh calibration validation.

Largest repair deltas:

- RB James Conner T48: 0.012790
- RB Alvin Kamara T48: 0.005405
- WR David Moore T24: 0.005119
- RB Christian McCaffrey T48: 0.004794
- WR Laquon Treadwell T24: 0.004724

Interpretation:

- Clamping removes the monotonicity contradictions in this internal benchmark.
- The repairs are small, but they alter probabilities.
- Because probabilities changed, Sprint 5AY calibration metrics do not apply to the repaired values.
- Clamping is not release-ready without new calibration, validation, leakage, coverage, and display-gate audits.

## 6. Coarse-Band Research Feasibility

5BC explored coarse-band feasibility only as aggregate internal research. No player-facing band table was created.

Candidate internal research bands were evaluated on clamped values only as aggregate counts:

- `internal_band_very_low`
- `internal_band_low`
- `internal_band_medium`
- `internal_band_high`
- `internal_band_very_high`

Findings:

- Aggregate band-count export was created for research review.
- No player-facing band output was created.
- No app-readable band table was created.
- No hidden sort key was created.
- No rank or decision artifact was created.
- The clamping benchmark produced no aggregate band shifts under the tested internal bands.

Implication: coarse-band research can continue internally, but banding does not fix calibration. Coarse-band app display remains blocked until a separate release gate proves monotonicity, calibration stability, coverage policy, schema safety, copy safety, and absence of hidden sort/rank behavior.

## 7. Ordinal/Cumulative Constrained-Model Feasibility

No ordinal/cumulative or shared constrained-threshold model was built in Sprint 5BC. That implementation is larger than this research comparison sprint and should not be rushed into a release path.

Feasibility assessment:

- This is the best long-term repair direction because it can encode threshold ordering in the model structure rather than patching independent outputs afterward.
- It should preserve the 5BB top-N-or-better semantics directly.
- It can potentially reduce or eliminate adjacent-threshold contradictions by design.
- It still requires full holdout validation, calibration audit, leakage/schema audit, coverage audit, and release-gate review.

Risks:

- Calibration remains unknown until trained and validated.
- Sparse top-threshold labels still need careful treatment.
- A constrained model can still be poorly calibrated even if monotonic.
- App display and exact percentages remain blocked until release gates pass.

Recommended future prototype: compare raw independent heads, clamped benchmark, and an ordinal/cumulative or shared constrained approach under the same train/validation/test split without producing app-readable outputs.

## 8. Calibration And Release-Gate Implications

Monotonicity repair is necessary but not sufficient.

Release implications by approach:

| Approach | Monotonicity result | Calibration status | Exact percentages | Coarse-band research | Release recommendation |
|---|---|---|---|---|---|
| Raw independent heads baseline | violations retained | 5AY unstable bins remain | blocked | internal-only with warnings | blocked |
| Post-hoc clamping benchmark | 0 RB/WR violations after clamp | prior calibration invalid for repaired values | blocked | useful internal benchmark | internal benchmark only |
| Coarse-band-only transformation | feasible only on monotonic repaired inputs | banding does not fix calibration | blocked | internal-only quarantined | research-only |
| Ordinal/cumulative constrained model | design should enforce chain | unknown until trained and validated | blocked until future validation | best future research candidate | feasible future research |

Required gates before any display discussion:

- monotonicity gate
- calibration gate
- coverage gate
- leakage/schema gate
- app-output gate
- display-gate audit
- no app-readable blocked artifacts
- no hidden sort keys
- no rankings/sorting contamination

Exact percentages remain blocked. App wiring remains blocked. Rankings and sorting remain blocked.

## 9. Recommended Next Sprint

Recommended next sprint: `Sprint 5BD - Internal Constrained Threshold Prototype Design`

Safe scope:

- research-only
- no app wiring
- no app-readable probability or band tables
- no promoted artifacts
- no player-facing probabilities or bands
- no rankings/sorting changes
- no fake scoring for waived, blocked, rookie, or kicker rows

5BD should design or prototype a constrained threshold approach and compare it against:

- raw independent heads
- post-hoc clamping benchmark
- abstention for sparse/unstable heads
- aggregate-only coarse-band feasibility

5BD must re-run monotonicity and calibration checks after any repair or model change.

## 10. Final Gate Label

Final gate label: `MONOTONIC_REPAIR_PROTOTYPE_INTERNAL_ONLY_CONTINUE`

Meaning:

- The local-only prototype comparison found no app artifact, leakage, ranking/sorting, or promotion risk in the current 5BC outputs.
- Post-hoc clamping can continue as an internal benchmark.
- Ordinal/cumulative or constrained-threshold modeling is the preferred future research path.
- Exact percentages remain blocked.
- App wiring remains blocked.
- Coarse-band research remains internal-only.
- No head is app-ready.
