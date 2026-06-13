# Sprint 5BE Constrained/Ordinal Prototype Plan

## 1. Executive Verdict

Verdict: `CONSTRAINED_ORDINAL_PROTOTYPE_PLAN_READY`

Sprint 5BE defines the internal-only prototype contract and test harness required before any constrained/ordinal threshold model implementation begins.

This plan does not train a model, release probabilities, create app-readable outputs, promote artifacts, or approve app wiring. It prepares Sprint 5BF to build a quarantined internal prototype with explicit tests for monotonicity, calibration, feature legality, coverage, and output safety.

Current release state:

- Exact percentages remain blocked.
- App wiring remains blocked.
- Player-facing bands remain blocked.
- Rankings and sorting remain blocked.
- Coarse-band research remains internal-only.
- No head is app-ready.

## 2. Prior Sprint Inputs

Sprint 5BB locked threshold semantics:

- Thresholds are top-N-or-better events.
- RB and WR must satisfy `P(T6) <= P(T12) <= P(T24) <= P(T36) <= P(T48)`.
- Threshold monotonicity is necessary before any display, sorting, app wiring, or artifact promotion can be considered.

Sprint 5BC found:

- RB raw independent heads: 3 violations across 3 players, max gap `0.012790`.
- WR raw independent heads: 27 violations across 15 players, max gap `0.002894`.
- Post-hoc clamping benchmark: 0 adjacent-pair violations after repair.
- Clamped outputs require fresh calibration validation.
- Clamping remains an internal benchmark only.

Sprint 5BD recommended:

- Prototype a cumulative/ordinal or shared constrained-threshold model internally.
- Keep post-hoc clamping as a benchmark.
- Continue abstention/no-display for sparse or unstable heads.
- Preserve all app, release, ranking, and artifact guardrails.

## 3. Prototype Scope

Allowed in Sprint 5BF:

- Internal-only prototype design and implementation.
- Local-only evaluation exports.
- Model comparison metrics.
- Monotonicity checks.
- Calibration checks.
- Leakage/schema checks.
- Coverage checks.
- Comparison against raw independent and post-hoc clamped baselines.

Not allowed in Sprint 5BF:

- App-readable outputs.
- Promoted model artifacts.
- Player-facing percentages.
- Player-facing bands.
- Ranking or sorting changes.
- Decision automation.
- Waived-player scoring without valid features.
- Blocked-player fake or placeholder scoring.
- Rookie scoring through veteran heads.
- Kicker scoring through veteran threshold heads.
- Use of forbidden features or label-leakage sources.

Forbidden prediction features remain forbidden:

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

## 4. Candidate Architecture

Preferred implementation path: build both candidate families if feasible, otherwise build the cumulative/ordinal path first and document the shared constrained path as a fallback.

### Candidate A: Cumulative/Ordinal Threshold Model

Design:

- Model top-N-or-better thresholds jointly.
- Derive nested threshold probabilities from one shared structure.
- Encode threshold order directly so wider thresholds cannot produce lower probabilities than narrower thresholds.

Monotonicity enforcement:

- The model should produce cumulative probabilities in threshold order.
- The test harness must still audit every player and adjacent threshold pair.
- Any violation is a prototype failure, even if caused by numerical precision or export transformation.

Feasibility:

- Semantically aligned with the 5BB top-N-or-better contract.
- Better suited than independent heads for nested threshold events.
- Sparse T6/T3 heads still require regularization, pooling, or abstention.
- Requires fresh calibration validation because structure and outputs differ from 5AY/5BC.

### Candidate B: Shared Constrained-Threshold Model

Design:

- Use a shared base risk/strength component across thresholds.
- Add threshold-specific intercepts or constrained adjustments.
- Enforce ordered thresholds through constraints or post-fit projection within the model pipeline.

Monotonicity enforcement:

- Threshold-specific components must be constrained so `P(T6) <= P(T12) <= P(T24) <= P(T36) <= P(T48)` for RB/WR.
- The test harness must audit the exported probabilities independently of model assumptions.

Feasibility:

- May be easier to implement with existing binary-head tooling.
- Can reduce independent-head contradictions by sharing signal.
- Still vulnerable to calibration instability and sparse-head overfitting.
- Must not be considered app-safe unless future validation and release gates pass.

### Required Baselines

Sprint 5BF must compare either constrained architecture against:

- raw independent 5AY-style heads
- post-hoc clamping benchmark
- abstention/no-display policy for sparse or unstable heads

## 5. Test Harness Specification

Sprint 5BF must include a test harness or deterministic audit script that verifies each of these checks:

| Check | Required assertion | Failure result |
|---|---|---|
| Legal feature schema only | Prototype feature names are from the approved renamed preseason/prior-season schema. | Block prototype result. |
| Forbidden feature scan | No ADP, public rankings, projections, consensus, market/trade values, prior fantasy draft history, RotoWire fields, `private_score`, same-season final stats, or label supplement features. | Block prototype result. |
| Split discipline | Training, calibration, validation, test, and current-player scoring are separated; no current 2026 rows fit model or calibration parameters. | Block prototype result. |
| Threshold semantics | All heads retain top-N-or-better meaning. | Block prototype result. |
| Monotonicity direction | RB/WR satisfy `P(T6) <= P(T12) <= P(T24) <= P(T36) <= P(T48)` for every scored player. | Block exact/coarse release discussion. |
| No app-readable output path | Outputs are only under the approved `local_exports` 5BF folder. | Block and quarantine. |
| No ranking/sorting output | No hidden sort keys, ranking fields, rank deltas, or model-driven ordering outputs are created. | Block and quarantine. |
| No promoted artifacts | No model artifact is saved outside local research exports or promoted package paths. | Block and quarantine. |
| No waived/unscored players scored | Waived, blocked, or missing-feature players remain unscored. | Block prototype result. |
| Rookies excluded from veteran heads | Rookie rows are not forced through veteran threshold heads. | Block prototype result. |
| Kickers not applicable | K rows are excluded or marked not applicable. | Block prototype result. |
| Calibration metrics are research-only | Metrics are written only as local research audit outputs. | Block app/release use. |
| Baseline comparison | Prototype is compared against raw independent and clamped baselines. | Incomplete prototype. |

Suggested harness outputs for Sprint 5BF:

- `feature_schema_audit.csv`
- `forbidden_feature_scan.csv`
- `split_discipline_audit.csv`
- `threshold_semantics_audit.csv`
- `monotonicity_audit.csv`
- `calibration_metrics_research_only.csv`
- `baseline_comparison_metrics.csv`
- `coverage_audit.csv`
- `sparse_head_audit.csv`
- `artifact_quarantine_audit.csv`
- `release_gate_blockers.csv`
- `README_SPRINT_5BF.md`

All harness outputs must be local-only and must explicitly state that they are not app-readable release artifacts.

## 6. Evaluation Metric Specification

Sprint 5BF must report, at minimum:

- Brier score, log loss, or equivalent proper probability metrics.
- Calibration-bin stability by position and threshold.
- Monotonicity violation count.
- Max monotonicity violation gap.
- Average monotonicity violation gap.
- Coverage counts:
  - ready veteran rows scored
  - blocked rows not scored
  - waived rows not scored
  - rookies excluded
  - kickers not applicable
- Sparse-head flags and support counts.
- Per-position threshold support:
  - eligible rows
  - events
  - non-events
  - train events
  - validation events
  - test events
- Calibration drift versus:
  - raw independent baseline
  - post-hoc clamped benchmark
  - empirical baseline
- Monotonicity change versus:
  - raw independent baseline
  - post-hoc clamped benchmark
- Abstention recommendations for sparse, unstable, or under-covered heads.

Metrics must be labeled research-only. Better metrics do not permit app wiring or release unless a separate release gate passes.

## 7. Artifact Quarantine Contract

All Sprint 5BF prototype outputs must be written only under:

`local_exports/outcome_probability/sprint_5bf_constrained_ordinal_internal_prototype/`

Required artifact rules:

- Outputs must remain local-only.
- Outputs must remain ignored and uncommitted unless a later instruction explicitly approves a report file.
- Outputs must not be app-readable.
- Outputs must not be imported by app code.
- Outputs must not be model artifacts.
- Outputs must not include player-facing percentages.
- Outputs must not include player-facing bands.
- Outputs must not include rankings/sorting fields.
- Outputs must not include decision recommendations.

Every row-level prototype output must include, or be accompanied by, these labels:

- `output_scope=internal_only_not_app_readable`
- `app_release_status=blocked_not_app_readable`
- `exact_percentage_display_allowed=no`
- `coarse_band_display_allowed=no`
- `sort_allowed=no`
- `ranking_use_allowed=no`
- `model_artifact_promoted=no`

If the prototype creates aggregate metrics only, the README and metadata must still use `internal_only_not_app_readable`.

## 8. Release-Gate Implications

A successful Sprint 5BF prototype does not release probabilities.

A successful prototype does not permit:

- app wiring
- exact percentage display
- coarse-band display
- rankings-table display
- sorting by model output
- decision automation
- promoted model artifacts
- app-readable probability or band tables

A successful prototype earns only a follow-up adversarial audit. Exact percentages remain blocked until a separate release gate passes. Coarse bands remain blocked until a separate coarse-band gate passes.

Minimum follow-up gate sequence after 5BF:

1. Adversarial prototype audit.
2. Calibration and monotonicity hardening audit.
3. Coverage and abstention policy audit.
4. App-output/display-gate audit.
5. Explicit release decision, if and only if all prior gates pass.

## 9. Recommended Sprint 5BF Implementation Prompt

Recommended prompt:

```text
Sprint 5BF - Internal Constrained/Ordinal Threshold Prototype

Build a local-only internal prototype comparing:
1. raw independent threshold heads
2. post-hoc clamped benchmark
3. cumulative/ordinal threshold model if feasible
4. shared constrained-threshold model if feasible
5. abstention/no-display policy for sparse or unstable heads

Use only legal renamed prior-season/preseason features.
Do not use ADP, public rankings, projections, consensus, market values, trade calculators, prior fantasy draft history, RotoWire fields, private_score, same-season final stats as preseason features, or label supplement sources as prediction features.

Write outputs only to:
local_exports/outcome_probability/sprint_5bf_constrained_ordinal_internal_prototype/

Every output must be internal_only_not_app_readable.
Do not wire probabilities into the app.
Do not create app-readable probability or band tables.
Do not promote artifacts.
Do not create fake probabilities.
Do not alter rankings/sorting.
Do not score waived, blocked, rookie, or kicker rows through the wrong path.

Run the required 5BE test harness:
- feature schema audit
- forbidden feature scan
- split discipline audit
- threshold semantics audit
- monotonicity audit
- calibration audit
- baseline comparison
- coverage audit
- sparse-head audit
- artifact quarantine audit
- release gate blocker report

Report whether constrained/ordinal research should continue, but keep exact percentages, app wiring, and coarse-band display blocked.
```

## 10. Final Gate Label

Final gate label: `CONSTRAINED_ORDINAL_PROTOTYPE_PLAN_READY`

Meaning:

- Sprint 5BF is ready for an internal-only prototype.
- Prototype outputs must be local-only and marked `internal_only_not_app_readable`.
- A successful prototype earns only a follow-up adversarial audit.
- Exact percentages remain blocked.
- App wiring remains blocked.
- Coarse bands remain blocked from app display.
- No head is app-ready.
