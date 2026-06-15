# Sprint 5DB: Phase 6 Production-Candidate Calibration And Sanity Audit

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_PRODUCTION_CANDIDATE_SANITY_AUDIT`

Sprint type: `AUDIT_ONLY_NO_NEW_MODELING_NO_RELEASE`

## 1. Scope

Sprint 5DB audited the 5DA local-only Phase 6 production-candidate historical modeling outputs. This sprint did not train new models, run current-player inference, create current-player probabilities, create exact display percentages, create coarse display bands, create app-readable outputs, wire app display, alter rankings/sorting, create hidden sort keys, create promoted artifacts, touch rookie files, edit or commit `data/`, stage or commit `local_exports/`, push, or deploy.

## 2. Inputs Audited

Tracked inputs:

- `docs/outcome_probability/BUILD_SPRINT_5DA_PHASE_6_LOCAL_ONLY_PRODUCTION_CANDIDATE_MODELING.md`
- `scripts/outcome_probability/run_sprint_5da_phase6_local_only_production_candidate_modeling.py`
- `scripts/outcome_probability/build_sprint_5cz_phase6_production_candidate_harness.py`

Local-only evidence audited:

`local_exports/outcome_probability/sprint_5da_phase6_local_only_production_candidate_modeling/`

Local-only files audited:

- `aggregate_metrics_by_head_fold_method.csv`
- `candidate_logistic_coefficients.csv`
- `feature_quarantine_audit.csv`
- `head_candidate_verdicts.csv`
- `metadata.json`
- `README.md`

## 3. Artifact Quarantine Result

Artifact quarantine result: pass.

All 5DA outputs are under:

`local_exports/outcome_probability/sprint_5da_phase6_local_only_production_candidate_modeling/`

No 5DA output was written to an app, Streamlit, app-loader, rankings, sorting, promoted, production artifact, `data/`, or app-readable path.

5DA exported aggregate historical evidence only. It did not export row-level player predictions, current-player predictions, exact display percentages, coarse bands, rankings signals, sorting keys, hidden sort keys, promoted artifacts, serialized model files, or production model artifacts.

## 4. Metadata And Output Flags

5DA metadata confirms:

- `output_scope=internal_only_not_app_readable`
- eligible heads only: true
- row-level predictions exported: false
- current-player inference performed: false
- current-player probabilities created: false
- app-readable outputs created: false
- serialized model artifacts created: false
- production model artifacts created: false
- exact display percentages created: false
- coarse display bands created: false
- app wiring created: false
- rankings/sorting created: false
- hidden sort keys created: false
- promoted artifacts created: false

## 5. Head Tiers After Audit

Accepted for Phase 7 display-contract planning only:

- `qb_t12`
- `rb_t12`
- `wr_t12`
- `wr_t24`
- `wr_t36`
- `te_t12`

These heads are accepted only as candidates for a future display-contract planning sprint. They are not approved for current-player inference, app output, exact percentages, coarse display bands, rankings/sorting, hidden sort keys, or promoted artifacts.

Caution heads remain excluded from the Phase 6 accepted set:

- `qb_t18`
- `qb_t24`
- `rb_t24`
- `te_t18`
- `te_t24`

Deferred heads remain deferred:

- `rb_t36`
- `rb_t48`
- `wr_t48`

Blocked heads remain blocked:

- `qb_t6`
- `rb_t6`
- `wr_t6`
- `te_t3`
- `te_t6`

## 6. Metrics Sanity

All six accepted heads produced four historical rolling folds and improved mean Brier and mean log loss relative to the training-fold base-rate baseline.

| Head | Mean AUC | Brier improvement vs base | Log-loss improvement vs base | Thin calibration bins | Audit tier |
| --- | ---: | ---: | ---: | ---: | --- |
| `qb_t12` | 0.863968 | 0.045909 | 0.140288 | 6 | accepted for contract planning |
| `rb_t12` | 0.857595 | 0.016949 | 0.057517 | 7 | accepted for contract planning |
| `wr_t12` | 0.911960 | 0.014858 | 0.055552 | 4 | accepted for contract planning |
| `wr_t24` | 0.871147 | 0.036341 | 0.112828 | 6 | accepted for contract planning |
| `wr_t36` | 0.861316 | 0.056323 | 0.154026 | 4 | accepted for contract planning |
| `te_t12` | 0.881903 | 0.032758 | 0.105345 | 8 | accepted for contract planning |

Sanity verdict: pass for local-only production-candidate review. The metrics are directionally stronger than the base-rate baseline, but they remain historical aggregate metrics and do not approve player-facing probabilities.

## 7. Calibration Audit

Maximum fold calibration gaps from the candidate logistic method:

| Head | Max calibration gap | Audit interpretation |
| --- | ---: | --- |
| `qb_t12` | 0.646958 | high gap; exact probabilities and bands remain blocked |
| `rb_t12` | 0.529152 | high gap; exact probabilities and bands remain blocked |
| `wr_t12` | 0.506245 | high gap; exact probabilities and bands remain blocked |
| `wr_t24` | 0.210736 | moderate gap; still not display-ready |
| `wr_t36` | 0.157622 | lower gap; still not display-ready |
| `te_t12` | 0.303062 | moderate gap; still not display-ready |

Calibration verdict: pass only for Phase 7 contract planning, not for display release. The gaps must be carried into the model card and any later display-contract sprint as explicit reasons to keep exact percentages and coarse bands blocked unless HQ separately approves a safer display format.

## 8. Support And Stability

Minimum fold support:

| Head | Min train positives | Min holdout positives | Support verdict |
| --- | ---: | ---: | --- |
| `qb_t12` | 67 | 11 | pass for local audit |
| `rb_t12` | 65 | 9 | pass with holdout-thin caution |
| `wr_t12` | 69 | 10 | pass for local audit |
| `wr_t24` | 133 | 20 | pass |
| `wr_t36` | 200 | 31 | pass |
| `te_t12` | 68 | 11 | pass for local audit |

Support verdict: sufficient for human-review and display-contract planning. The support is not sufficient to approve current-player probabilities or display bands.

## 9. Leakage And Feature Quarantine

Feature quarantine result: pass.

Forbidden feature matches: 0.

The 5DA feature audit used only the approved source-safe prior completed-season feature allowlist. It did not use target-season/future features, display fields, ADP, projections, public rankings, consensus, market values, trade values/calculators, RotoWire values, fantasy totals, EPA, WOPR/RACR/PACR/Dakota, target-share fields, prior fantasy draft history, legacy `private_score`, or same-season target stats as features.

No current-player, current-board, latest-season, app-readable, rookie, or release-service path was used.

## 10. Overfitting And Model-Family Audit

The candidate model remains low-complexity logistic evaluation over deterministic rolling folds. No broad hyperparameter search was performed. The script emits coefficient diagnostics for human review but no serialized model artifact.

Overfitting verdict: pass for local-only audit. Future review must continue to inspect coefficient signs and fold-by-fold drift before any display semantics are proposed.

## 11. Phase 7 Proposal Eligibility

Phase 7 display-contract planning may be proposed next with the accepted six-head set, subject to these constraints:

- Phase 7 may define a display contract only.
- Phase 7 must not wire app display unless a later HQ sprint explicitly approves it.
- Exact display percentages remain blocked.
- Coarse display bands remain blocked.
- Current-player inference remains blocked.
- Rankings/sorting and hidden sort keys remain blocked.
- Promoted artifacts remain blocked.

## 12. Gate Verdict

5DB verdict: GREEN.

The accepted heads are defensible for a future display-contract planning sprint, all outputs remain quarantined, no current-player inference occurred, no app-readable files exist, and no leakage/provenance/app/rookie contamination appeared.

## 13. Checks

Checks run:

- repo/path/branch/status/log preflight passed
- 5DA local-only metadata audit passed
- 5DA local-only file inventory audit passed
- 5DA feature quarantine audit passed
- 5DA metrics, calibration, and support audit completed
- `git diff --check` passed

No Python files changed in 5DB, so `python -m py_compile`, Ruff, and pytest were not required.
