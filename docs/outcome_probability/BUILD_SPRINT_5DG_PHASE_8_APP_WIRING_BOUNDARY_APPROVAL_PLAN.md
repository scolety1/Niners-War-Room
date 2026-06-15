# Sprint 5DG: Phase 8 App-Wiring Boundary And Approval Plan

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_PROCEED_TO_STATIC_APP_SURFACE_INVENTORY`

Sprint type: `DOCS_ONLY_PHASE_8_BOUNDARY_PLAN_NO_APP_EDIT`

## 1. Scope

Sprint 5DG defines the boundary for a future Phase 8 app-wiring packet. This sprint is planning only. It does not approve app wiring, does not create an app-readable schema or output, and does not modify app/source files.

This sprint did not create app-readable outputs, JSON/CSV/parquet display artifacts, current-player inference, current-player probabilities, exact display percentages, coarse display bands, model training, production model artifacts, app wiring, rankings/sorting changes, hidden sort keys, promoted artifacts, rookie file changes, `data/` changes, `local_exports/`, push, deploy, internet lookup, or package installs.

## 2. Inputs Reviewed

5DG starts from:

- `docs/outcome_probability/BUILD_SPRINT_5DE_PHASE_7_OUTCOME_DISPLAY_CONTRACT_PLANNING.md`
- `docs/outcome_probability/BUILD_SPRINT_5DF_PHASE_7_LOCAL_ONLY_DISPLAY_CONTRACT_ARTIFACT_DESIGN.md`
- last completed commit `ba97c12 Design Phase 7 outcome display contract artifact`

## 3. Future App-Wiring Boundary

A future Phase 8 app-wiring packet may only be proposed after static inventory and QA planning complete GREEN. Even then, app wiring would need an explicit HQ approval prompt before any source file is edited.

The future boundary must stay limited to:

- non-numeric Outcome model status only
- the approved status vocabulary
- the accepted display-planning heads only
- a separately approved app-readable status source, if HQ later authorizes one
- tests proving no numeric, sorting, hidden-key, probability, band, or promotion leakage

The future boundary must not include:

- exact probabilities
- coarse bands
- model scores
- model ranks
- player ordering
- hidden status weights
- hidden sort keys
- promoted artifacts
- current-player inference unless separately approved

## 4. App/Source Surfaces To Inventory First

Before any UI work, a read-only inventory must identify:

- app entry points and Streamlit/page files
- player table or player-card rendering surfaces
- data loader and service boundaries
- status/metadata display surfaces
- filtering, sorting, ranking, and export paths
- tests covering app display and data loading
- any cache/download path that could leak model internals

Inventory must be read-only. No app/source files may be edited during inventory.

## 5. Allowed Non-Numeric Status Concept

The only allowed future user-facing concept remains:

`non_numeric_status_only`

Approved vocabulary for planning only:

- `internal_review_passed`
- `under_review`
- `unavailable`

Approved copy family:

- `Outcome model: internal review passed`
- `Outcome model: under review`
- `Outcome model: unavailable`

This vocabulary must not become an implicit ranking, score, probability bucket, color ramp, sort key, or player-comparison feature.

## 6. Eligible Planning Heads

Only these heads remain eligible for future display planning:

- `qb_t12`
- `rb_t12`
- `wr_t12`
- `wr_t24`
- `wr_t36`
- `te_t12`

Caution, deferred, blocked, unknown, or unapproved heads must fail closed.

## 7. Blocked Numeric And Output Paths

Still blocked:

- exact percentages
- coarse display bands
- current-player inference
- current-player probabilities
- app-readable status/probability/band files
- JSON/CSV/parquet display artifacts
- rankings/sorting
- hidden sort keys
- promoted artifacts
- production model artifacts

No future code file may be touched until HQ explicitly approves an app-wiring sprint after the planning/readiness gates.

## 8. Approval Checkpoints Before Code Changes

Before any code file can be touched in a future sprint, these checkpoints must pass:

1. 5DH static app surface inventory is GREEN.
2. 5DI non-numeric QA contract is GREEN.
3. 5DJ readiness verdict is GREEN.
4. HQ explicitly approves a Phase 8 app-wiring packet.
5. Exact file allowlist for code edits is provided.
6. App-readable schema, if any, is explicitly authorized.
7. Tests are specified before implementation.
8. Rollback and kill-switch behavior is documented.
9. Sorting/ranking/hidden-key blockers remain explicit.
10. `data/` and `local_exports/` remain uncommitted.

## 9. Rollback And Stop Rules

Stop immediately if any future sprint:

- touches app/source files without explicit approval
- creates app-readable output without explicit approval
- creates probabilities, percentages, bands, scores, ranks, or hidden keys
- creates current-player inference without explicit approval
- touches rookie files
- stages `data/` or `local_exports/`
- creates promoted artifacts
- modifies rankings/sorting
- finds uncertainty in schema ownership or display semantics

Rollback must remove or quarantine any unauthorized artifact and leave no app-readable residue.

## 10. Recommendation

5DG recommendation: GREEN.

Static app surface inventory may proceed next as a read-only docs-only audit. App wiring remains blocked.

## 11. Checks

Checks run:

- repo/path/branch/status/log preflight passed
- `git diff --check` passed

No Python files changed in 5DG, so `python -m py_compile`, Ruff, and pytest were not required.
