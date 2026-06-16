# Sprint 5CS: Phase 5 Local Model Candidate Proposal

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_PROPOSE_LOCAL_ONLY_CANDIDATE_MODELING_NEXT`

Sprint type: `PHASE_5_PROPOSAL_ONLY_NO_MODELING_NO_RELEASE`

## 1. Scope

Sprint 5CS proposes what a future local-only Phase 5 candidate modeling sprint may evaluate. This sprint is proposal/design only. It did not train models, create production model artifacts, create current-player probabilities, create exact display percentages, create coarse bands, create app-readable outputs, wire app display, alter rankings/sorting, create hidden sort keys, create promoted artifacts, touch rookie files, edit `data/`, stage or commit `local_exports/`, push, or deploy.

No script was required. No local-only export was created.

## 2. Evidence Base

5CS is based on the completed Phase 4 local shadow evaluation through 5CR:

- 5CN: local shadow model preflight and eligible-head design gate
- 5CO: local-only aggregate shadow model evaluation
- 5CP: backtest, calibration, and sanity audit
- 5CQ: human review packet, no app output
- 5CR: Phase 5 readiness verdict

The last committed Phase 4 verdict is:

`c1709e9 Record Phase 5 readiness verdict`

Phase 5 is approved to propose next, not run.

## 3. First Phase 5 Candidate Heads

The first Phase 5 local candidate set should include exactly these 11 heads:

| Short name | Canonical head | Position | Inclusion reason |
| --- | --- | --- | --- |
| `qb_t12` | `same_year_qb_t12` | QB | viable in 5CP, strong enough for human-review continuation |
| `qb_t18` | `same_year_qb_t18` | QB | viable in 5CP, requires calibration-bin caution |
| `qb_t24` | `same_year_qb_t24` | QB | viable in 5CP, requires calibration-bin caution |
| `rb_t12` | `same_year_rb_t12` | RB | viable in 5CP |
| `rb_t24` | `same_year_rb_t24` | RB | viable in 5CP |
| `wr_t12` | `same_year_wr_t12` | WR | viable in 5CP |
| `wr_t24` | `same_year_wr_t24` | WR | viable in 5CP |
| `wr_t36` | `same_year_wr_t36` | WR | viable in 5CP |
| `te_t12` | `same_year_te_t12` | TE | viable in 5CP |
| `te_t18` | `same_year_te_t18` | TE | viable in 5CP, requires calibration-bin caution |
| `te_t24` | `same_year_te_t24` | TE | viable in 5CP, requires calibration-bin caution |

These heads may be proposed for a future local-only candidate modeling sprint. 5CS does not approve running that sprint.

## 4. Deferred Weak/Caution Heads

The following weak/caution heads should be excluded from the first Phase 5 candidate set and deferred:

- `rb_t36` / `same_year_rb_t36`
- `rb_t48` / `same_year_rb_t48`
- `wr_t48` / `same_year_wr_t48`

Rationale:

- `rb_t36` and `rb_t48` showed weaker aggregate AUC and higher Brier than the stronger RB heads.
- `wr_t48` was informative but weaker than WR Top 12/24/36.
- Broad threshold semantics may be harder to review and more likely to create misleading display interpretations later.

These heads may only be separately evaluated after HQ approves a targeted broad-threshold caution sprint.

## 5. Still-Blocked Heads

The following heads remain blocked/not evaluated:

- `qb_t6` / `same_year_qb_t6`
- `rb_t6` / `same_year_rb_t6`
- `wr_t6` / `same_year_wr_t6`
- `te_t3` / `same_year_te_t3`
- `te_t6` / `same_year_te_t6`

These heads remain blocked because Phase 4 found constrained/sparse support patterns. They must not be included in the first Phase 5 candidate modeling sprint.

## 6. Anti-Leakage Rules

Any future candidate modeling sprint must enforce:

1. completed prior-season features only
2. same-season final stats as labels only, never preseason features
3. no current-player or current-board scoring
4. no rookie scoring through veteran heads
5. no target-year outcome leakage in features
6. no label supplement sources as prediction features
7. no fantasy totals as features
8. no EPA, WOPR, RACR, PACR, Dakota, target-share, or air-yard-share features
9. no ADP, public rankings, projections, consensus, market values, trade values/calculators, RotoWire rankings/projections/outlooks/values, prior fantasy draft history, or legacy `private_score`
10. preserve the 5CK-R accepted Taysom Hill source/target position mismatch exclusion unless HQ approves a specific multi-position policy

## 7. Allowed Source Packages And Historical Seasons

Allowed historical target seasons:

- 2010 through 2019 only

Allowed local source packages:

- `local_exports/outcome_probability/sprint_5ci_2010_2011_historical_feature_label_rebuild/`
- `local_exports/outcome_probability/sprint_5cf_2012_2013_historical_feature_label_rebuild/`
- `local_exports/outcome_probability/sprint_5cc_2014_2015_historical_feature_label_rebuild/`
- `local_exports/outcome_probability/sprint_5bz_2016_2017_historical_feature_label_rebuild/`
- `local_exports/outcome_probability/sprint_5bv_2018_2019_historical_feature_label_rebuild/`
- consolidated 5CK-R2/5CL/5CO local-only aggregate evidence for audit context only

Allowed feature family:

- 5CN-approved prior completed-season source-safe features only

No `data/` path may be edited, staged, cleaned, deleted, or committed.

No `local_exports/` path may be staged or committed.

## 8. Backtest And Evaluation Strategy

The first Phase 5 candidate modeling sprint should use a locked time-aware evaluation plan:

| Fold | Training target seasons | Validation/holdout target season |
| --- | --- | ---: |
| 1 | 2010-2015 | 2016 |
| 2 | 2010-2016 | 2017 |
| 3 | 2010-2017 | 2018 |
| 4 | 2010-2018 | 2019 |

No random split is allowed.

The future sprint may compare:

- training-fold base-rate baseline
- prior NWR finish-rank baseline
- prior NWR PPG baseline
- low-complexity logistic candidate
- one additional low-complexity model only if it is source-safe, deterministic, locally available, and not a broad hyperparameter search

No production model artifact may be created.

## 9. Minimum Support Thresholds

Before a head may run in the future candidate sprint, it must satisfy all support gates already met in 5CL/5CP:

- at least 10 historical target seasons represented
- at least 50 positive labels across 2010-2019 for QB/RB/WR/TE candidate heads
- at least 300 eligible labeled rows for the position/head
- no one-class holdout fold for the candidate head
- no unresolved non-missing-label blocker except the committed 5CK-R accepted Taysom Hill exclusion

If any head fails these checks when rerun, the future sprint must mark that head blocked and continue only if at least one other candidate head remains valid.

## 10. Calibration And Sanity Gates

A future local candidate modeling sprint must pass:

- aggregate calibration-bin audit by head and holdout season
- thin-bin reporting with no forced display interpretation
- Brier and log-loss comparison against base rate
- AUC and PR-AUC where computable
- directional sanity audit of coefficients/importance
- position-specific sanity review
- small-sample and class-imbalance review
- temporal drift review
- too-good-to-be-true leakage audit
- abstention recommendation by head

Any head with unstable calibration, weak support, suspicious leakage indicators, or misleading semantics must be blocked from further display-path consideration.

## 11. Overfitting Guardrails

The future candidate sprint must not perform broad hyperparameter search.

Required guardrails:

- predeclare features and heads before modeling
- use the same locked rolling holdout folds
- use simple deterministic methods first
- compare against source-safe baselines
- avoid per-head tuning beyond documented defaults
- do not select heads based on post-hoc holdout performance alone
- report weak results honestly
- do not create production model files or reusable app artifacts

## 12. Output Quarantine Rules

Allowed future local-only outputs may exist only under a new sprint-specific ignored directory such as:

`local_exports/outcome_probability/sprint_5ct_local_only_model_candidate_evaluation/`

Allowed output types for the future sprint:

- aggregate metrics by head/fold/method
- calibration summaries by head/fold
- feature allowlist audit
- forbidden-field scan
- coefficient/importance diagnostics by head/fold
- metadata with release blockers
- README summary

Forbidden output types:

- row-level predicted probability exports
- player-level probability exports
- current-player probability exports
- app-readable probability, band, or status tables
- exact display percentages
- coarse display bands
- production model artifacts
- pickled promoted models
- ranking/sorting outputs
- hidden sort keys
- app loader files
- Streamlit/app files

## 13. Future Candidate Sprint File Contract

A future local-only candidate modeling sprint may create only these tracked files:

- `docs/outcome_probability/BUILD_SPRINT_5CT_LOCAL_ONLY_MODEL_CANDIDATE_EVALUATION.md`
- `scripts/outcome_probability/build_sprint_5ct_local_only_model_candidate_evaluation.py`

It may create ignored local-only outputs only under:

- `local_exports/outcome_probability/sprint_5ct_local_only_model_candidate_evaluation/`

Files and directories that remain forbidden:

- `data/`
- `local_exports/` staging or commits
- rookie framework files
- Streamlit/app files
- app loader/release service files
- rankings/sorting/value pipeline files
- promoted artifact directories
- production model artifact directories
- current-board/current-player output paths

## 14. Release And Display Blockers

Current-player probabilities remain blocked.

Exact display percentages remain blocked.

Coarse display bands remain blocked.

App wiring remains blocked.

Rankings/sorting remain blocked.

Hidden sort keys remain blocked.

Promoted artifacts remain blocked.

Production model artifacts remain blocked.

No app-readable probability, band, or status output is approved.

## 15. Recommendation

5CS recommendation: GREEN.

A future local-only candidate modeling sprint may be proposed next, using the exact first candidate set and quarantine contract defined in this document.

5CS does not approve running that future sprint.

## 16. Checks

Checks run:

- repo/path/branch/status/log preflight passed
- Phase 4 readiness and audit docs reviewed
- `git diff --check` passed

No Python files changed in 5CS, so `python -m py_compile`, Ruff, and pytest are not required.
