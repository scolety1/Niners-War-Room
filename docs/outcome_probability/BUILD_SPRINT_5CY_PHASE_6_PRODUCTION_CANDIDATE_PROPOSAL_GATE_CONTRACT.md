# Sprint 5CY: Phase 6 Production-Candidate Proposal Gate Contract

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_PROPOSE_PHASE_6_LOCAL_ONLY_PRODUCTION_CANDIDATE_PACKET`

Sprint type: `PHASE_6_PROPOSAL_ONLY_NO_MODELING_NO_RELEASE`

## 1. Scope

Sprint 5CY defines the proposal and gate contract for a future Phase 6 local-only production-candidate modeling packet. This sprint is proposal/design only. It did not train models, run production-candidate modeling, create production model artifacts, run current-player inference, create current-player probabilities, create exact display percentages, create coarse bands, create app-readable outputs, wire app display, alter rankings/sorting, create hidden sort keys, create promoted artifacts, touch rookie files, edit or commit `data/`, stage or commit `local_exports/`, push, deploy, or install packages.

No script was required. No local-only export was created.

## 2. Evidence Base

5CY starts from the completed Phase 5 local-only candidate modeling packet through:

- `5CT` local-only candidate modeling harness
- `5CU` local-only candidate model evaluation
- `5CV` candidate model calibration and sanity audit
- `5CW` human review packet and candidate model card
- `5CX` Phase 5 production-proposal readiness verdict

Last completed commit:

`b982278 Record Phase 5 candidate modeling verdict`

Phase 6 is approved to propose next, not run.

## 3. Eligible First Phase 6 Heads

The first Phase 6 production-candidate proposal should include exactly these heads:

| Short head | Canonical head | Position | Policy |
| --- | --- | --- | --- |
| `qb_t12` | `same_year_qb_t12` | QB | eligible for first Phase 6 local-only production-candidate packet |
| `rb_t12` | `same_year_rb_t12` | RB | eligible for first Phase 6 local-only production-candidate packet |
| `wr_t12` | `same_year_wr_t12` | WR | eligible for first Phase 6 local-only production-candidate packet |
| `wr_t24` | `same_year_wr_t24` | WR | eligible for first Phase 6 local-only production-candidate packet |
| `wr_t36` | `same_year_wr_t36` | WR | eligible for first Phase 6 local-only production-candidate packet |
| `te_t12` | `same_year_te_t12` | TE | eligible for first Phase 6 local-only production-candidate packet |

These heads are eligible only for a future local-only production-candidate modeling packet. They are not approved for app display, current-player inference, exact display percentages, coarse bands, rankings/sorting, hidden sort keys, or promoted artifacts.

## 4. Caution, Deferred, And Blocked Head Policy

Caution heads must stay out of the first production-candidate set unless HQ explicitly creates a separate caution-only evaluation lane:

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

A future Phase 6 packet must fail closed if any caution, deferred, blocked, unknown, or unapproved head is requested as part of the first production-candidate set.

## 5. Allowed Future Phase 6 Scope

A future Phase 6 local-only production-candidate modeling packet may:

1. train and evaluate candidate models only on historical 2010-2019 feature/label rows
2. use the accepted first Phase 6 heads only
3. use deterministic time-aware rolling folds or a stricter documented historical split
4. compare against historical base-rate, prior-rank, and prior-PPG baselines
5. create local-only production-candidate model artifacts if the Phase 6 sprint explicitly allows them
6. create aggregate metrics, calibration summaries, model cards, and audit evidence under a quarantined local-only directory
7. run model-card and human-review checks before any later proposal

A future Phase 6 packet must not:

- run current-player inference
- create current-board outputs
- create app-readable outputs
- create display probabilities or bands
- wire app display
- create ranking/sorting signals
- create hidden sort keys
- promote artifacts
- touch rookie files

## 6. Local-Only Artifact Policy

A future Phase 6 packet may allow local-only production-candidate artifacts only if they remain quarantined under a sprint-specific ignored directory, for example:

`local_exports/outcome_probability/sprint_5cz_phase6_local_only_production_candidate_modeling/`

Allowed local-only artifact types may include:

- aggregate metrics by head/fold/method
- calibration summaries by head/fold
- feature allowlist audit
- forbidden-field scan
- model-card JSON or markdown
- human-review checklist
- model coefficient or feature-importance diagnostics
- serialized local-only model candidates only if the Phase 6 sprint explicitly allows them

If serialized local-only model candidates are allowed in Phase 6, they must remain:

- under `local_exports/outcome_probability/<phase6_sprint>/`
- not app-readable
- not promoted
- not committed
- not loaded by app, rankings, sorting, or release services

Production model artifacts remain blocked by 5CY.

## 7. Strict Output Quarantine

Forbidden output paths and artifact types:

- `data/`
- committed `local_exports/`
- app or Streamlit paths
- app loader paths
- rankings/sorting/value pipeline paths
- promoted artifact directories
- production model artifact directories
- current-board/current-player output paths
- app-readable probability, band, or status tables
- exact display percentage outputs
- coarse display band outputs
- hidden sort-key outputs

Every future Phase 6 output must carry or document:

- `output_scope=internal_only_not_app_readable`
- app release status blocked
- current-player inference false
- exact display percentages blocked
- coarse display bands blocked
- app wiring blocked
- rankings/sorting blocked
- hidden sort keys blocked
- promoted artifacts blocked

## 8. No Current-Player Inference Rule

Future Phase 6 work must not run current-player inference.

Allowed rows:

- historical target seasons 2010-2019 only
- completed prior-season source-safe features only

Forbidden rows:

- 2026 or current pool rows
- current-board rows
- current-player feature rows
- rookie rows scored through veteran heads

Any future script must fail closed if target seasons outside the approved historical window are requested.

## 9. Display And App Blockers

The following remain blocked:

- current-player probabilities
- exact display percentages
- coarse display bands
- app-readable probability outputs
- app-readable band outputs
- app-readable status outputs from this research lane
- app wiring
- rankings/sorting
- hidden sort keys
- promoted artifacts

No Phase 6 local-only artifact may be displayed, ranked, sorted, loaded by the app, or treated as production output.

## 10. Model-Card And Human-Review Requirements

A future Phase 6 packet must create or update:

- candidate model card
- feature/source restrictions section
- intended-use and non-use section
- historical coverage section
- eligible/caution/deferred/blocked head list
- calibration and sanity section
- leakage and forbidden-field scan section
- output quarantine section
- rollback/abandon section
- human-review checklist

Human review must happen before any Phase 7 display-contract proposal.

## 11. Calibration And Sanity Acceptance Gates

A future Phase 6 packet must pass all of these gates before any later Phase 7 proposal:

- Brier and log-loss comparison against base-rate baseline by head
- AUC and PR-AUC where computable
- calibration-bin audit by head and fold
- thin-bin reporting and abstention recommendation
- coefficient or feature-importance sanity review
- position-specific sanity review
- temporal drift review
- too-good-to-be-true leakage audit
- support and class-balance audit
- head-level accept/caution/reject verdict

No exact display percentages or coarse display bands may be proposed from Phase 6 unless a later HQ sprint explicitly approves a separate display contract path.

## 12. Overfitting And Leakage Guardrails

Required guardrails:

- predeclare head list and feature allowlist before any run
- use completed prior-season features only
- use same-season final stats as labels only
- do not use label supplement sources as features
- do not use target-year outcomes as features
- do not use current-season features
- avoid broad hyperparameter search
- compare against simple source-safe baselines
- preserve deterministic rolling historical folds
- report weak or failed results honestly
- do not select heads only by post-hoc holdout performance
- keep caution/deferred/blocked heads out unless separately approved

Forbidden features remain:

- fantasy totals
- EPA
- WOPR/RACR/PACR/Dakota
- target-share or air-yard-share fields
- ADP
- projections
- public rankings
- consensus
- market/trade values
- RotoWire rankings/projections/outlooks/values
- prior fantasy draft history
- legacy `private_score`
- same-season final stats as preseason features

## 13. Rollback And Abandon Criteria

A future Phase 6 packet must abandon or block any head if:

- calibration is unstable
- holdout support is too thin
- metrics fail to beat base-rate baseline
- leakage is suspected
- output quarantine fails
- current-player inference occurs
- app-readable output is created
- serialized artifacts appear outside the allowed local-only directory
- rankings/sorting or hidden sort keys are introduced
- human review finds misleading semantics

Rollback must include deleting or quarantining any local-only artifacts from the failed run and leaving no app-readable or promoted residue.

## 14. Phase 7 Preconditions

Before any later Phase 7 display-contract sprint can be proposed, all of the following must be true:

1. Phase 6 local-only production-candidate packet completes GREEN.
2. Candidate model card is complete.
3. Human review is complete.
4. Accepted heads are explicitly named.
5. Calibration and abstention gates pass.
6. No app-readable output exists.
7. No current-player inference exists unless a future HQ sprint explicitly authorizes a local-only non-app inference packet.
8. Exact display percentages remain blocked unless separately approved.
9. Coarse display bands remain blocked unless separately approved.
10. App wiring remains blocked unless separately approved.
11. Rankings/sorting and hidden sort keys remain blocked unless separately approved.
12. Promoted artifacts remain blocked unless separately approved.

## 15. Recommendation

5CY recommendation: GREEN.

A future Phase 6 local-only production-candidate modeling packet may be proposed next, using the six eligible heads and gate contract defined here.

5CY does not approve running Phase 6.

## 16. Checks

Checks run:

- DOCX prompt extracted and followed
- repo/path/branch/status/log preflight passed
- `git diff --check` passed

No Python files changed in 5CY, so `python -m py_compile`, Ruff, and pytest are not required.
