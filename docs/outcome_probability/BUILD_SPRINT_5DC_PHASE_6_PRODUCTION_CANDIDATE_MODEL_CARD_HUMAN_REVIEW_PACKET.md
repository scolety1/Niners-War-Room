# Sprint 5DC: Phase 6 Production-Candidate Model Card And Human Review Packet

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_MODEL_CARD_HUMAN_REVIEW_PACKET`

Sprint type: `DOCS_ONLY_MODEL_CARD_NO_NEW_MODELING_NO_RELEASE`

## 1. Scope

Sprint 5DC creates the model-card and human-review packet for the six heads accepted by the 5DB audit. This sprint did not train models, run current-player inference, create current-player probabilities, create exact display percentages, create coarse display bands, create app-readable outputs, wire app display, alter rankings/sorting, create hidden sort keys, create promoted artifacts, touch rookie files, edit or commit `data/`, stage or commit `local_exports/`, push, or deploy.

No script was created. No local-only export was created.

## 2. Inputs Reviewed

5DC reviewed:

- `docs/outcome_probability/BUILD_SPRINT_5CY_PHASE_6_PRODUCTION_CANDIDATE_PROPOSAL_GATE_CONTRACT.md`
- `docs/outcome_probability/BUILD_SPRINT_5CZ_PHASE_6_LOCAL_ONLY_PRODUCTION_CANDIDATE_PREFLIGHT_HARNESS.md`
- `docs/outcome_probability/BUILD_SPRINT_5DA_PHASE_6_LOCAL_ONLY_PRODUCTION_CANDIDATE_MODELING.md`
- `docs/outcome_probability/BUILD_SPRINT_5DB_PHASE_6_PRODUCTION_CANDIDATE_CALIBRATION_SANITY_AUDIT.md`
- `local_exports/outcome_probability/sprint_5da_phase6_local_only_production_candidate_modeling/`

## 3. Intended Use

Allowed intended use:

- internal human review of historical aggregate model evidence
- future Phase 7 display-contract planning proposal
- discussion of non-app display semantics and safety constraints

Forbidden use:

- current-player inference
- current-player probability generation
- exact display percentage generation
- coarse display band generation
- player-card display
- app-readable probability, band, or status outputs
- rankings/sorting
- hidden sort keys
- promoted artifacts
- production artifact publication
- rookie scoring through veteran heads

## 4. Accepted Heads

Accepted for Phase 7 display-contract planning only:

| Head | Canonical head | Position | Reason accepted |
| --- | --- | --- | --- |
| `qb_t12` | `same_year_qb_t12` | QB | four folds, Brier/log-loss improvement, support sufficient for planning |
| `rb_t12` | `same_year_rb_t12` | RB | four folds, Brier/log-loss improvement, support sufficient with holdout-thin caution |
| `wr_t12` | `same_year_wr_t12` | WR | four folds, strongest AUC, Brier/log-loss improvement |
| `wr_t24` | `same_year_wr_t24` | WR | four folds, Brier/log-loss improvement, moderate calibration gap |
| `wr_t36` | `same_year_wr_t36` | WR | four folds, Brier/log-loss improvement, strongest support among accepted heads |
| `te_t12` | `same_year_te_t12` | TE | four folds, Brier/log-loss improvement, support sufficient for planning |

Accepted here means accepted for human-review and display-contract planning only. It does not mean approved for release, display, production, app loading, current-player inference, percentages, bands, rankings, sorting, hidden keys, or promotion.

## 5. Excluded Heads

Caution heads remain excluded:

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

These heads must not be included in any Phase 7 display-contract proposal unless HQ creates a separate approved sprint to revisit them.

## 6. Historical Sources And Features

Historical target seasons:

- 2010-2019 only

Source policy:

- completed prior-season source-safe features only
- same-season final stats used only as labels
- no current-player or latest-season rows
- no rookie rows scored through veteran heads

Approved feature allowlist:

- `prior_completed_season_games`
- `prior_completed_season_games_active`
- `prior_completed_season_games_played`
- `prior_completed_season_passing_yards`
- `prior_completed_season_receiving_first_downs`
- `prior_completed_season_receiving_yards`
- `prior_completed_season_receptions`
- `prior_completed_season_rushing_first_downs`
- `prior_completed_season_rushing_yards`
- `prior_season_nwr_finish_rank`
- `prior_season_nwr_ppg`

## 7. Excluded And Forbidden Features

Forbidden as prediction features:

- same-season target stats
- label supplement sources
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
- current-player/current-board fields
- app display fields

The 5DA feature quarantine audit found 0 forbidden feature matches.

## 8. Model Family, Splits, And Evaluation

Model family:

- low-complexity logistic candidate model

Baselines:

- training-fold base-rate baseline
- source-safe prior-rank score baseline
- source-safe prior-PPG score baseline

Deterministic rolling folds:

| Fold | Training target seasons | Holdout target season |
| --- | --- | ---: |
| 1 | 2010-2015 | 2016 |
| 2 | 2010-2016 | 2017 |
| 3 | 2010-2017 | 2018 |
| 4 | 2010-2018 | 2019 |

No broad hyperparameter search was performed. No serialized model artifact was created.

## 9. Calibration, Sanity, And Stability

5DB found all six accepted heads improved mean Brier and mean log loss versus the training-fold base-rate baseline.

Calibration caveat:

- `qb_t12`, `rb_t12`, and `wr_t12` showed high maximum fold calibration gaps.
- `wr_t24`, `wr_t36`, and `te_t12` showed lower or moderate maximum fold calibration gaps, but still are not display-ready.

Model-card interpretation:

- the six heads are suitable for Phase 7 display-contract planning
- exact percentages remain blocked
- coarse display bands remain blocked
- any future display contract must represent uncertainty honestly and cannot imply calibrated player-facing probabilities

## 10. Failure Modes And Known Risks

Known risks:

- calibration gaps remain too large for exact display probabilities
- some folds have thin holdout positives
- source-era drift may affect stability
- position-specific support varies
- low-complexity coefficients need human review before any semantic display language is considered
- display semantics may mislead users if they imply ranking, sorting, or precise odds

Rollback/abandon triggers for future work:

- any current-player inference
- any app-readable output
- any exact percentage or coarse band output
- any hidden sort key or rankings/sorting signal
- any promoted or production artifact
- any leakage signal
- any feature outside the allowlist
- any rookie contamination

## 11. Human Review Checklist

Before Phase 7 display-contract planning can move beyond proposal, a human reviewer should inspect:

1. accepted head list and exclusions
2. feature allowlist and forbidden-field audit
3. fold-by-fold metrics and calibration gaps
4. coefficient diagnostics for football sanity
5. whether display wording can avoid implying exact odds
6. whether any display contract can remain non-sorting and non-ranking
7. whether the app should remain status-only until a later HQ sprint approves display
8. whether exact percentages and coarse bands should remain blocked
9. whether current-player inference should remain blocked
10. whether all local evidence remains quarantined

## 12. What Must Not Be Shown In The App

Still blocked from app display:

- exact outcome percentages
- coarse outcome bands
- production-candidate metrics
- historical aggregate model diagnostics
- row-level or player-level probabilities
- hidden model scores
- sorting/ranking keys
- model-card internals
- local-only export contents

Existing status-only Outcome Model Status copy remains the only safe app stance unless HQ separately approves a later display-contract sprint and implementation sprint.

## 13. Open Display-Format Questions

Open questions for a future Phase 7 display-contract planning sprint:

- whether any non-numeric status label could be safe
- whether display should remain entirely status-only
- whether human-review-only reports are the better path
- whether any model-card field can be summarized without becoming an implicit ranking signal
- what extra calibration evidence would be required before exact percentages or coarse bands could be reconsidered

## 14. Gate Verdict

5DC verdict: GREEN.

The model-card and human-review packet is complete, contains no app-readable outputs, contains no current-player probabilities, and preserves all display blockers. Sprint 5DD may proceed as a verdict/planning sprint.

## 15. Checks

Checks run:

- repo/path/branch/status/log preflight passed
- 5DA/5DB evidence review completed
- `git diff --check` passed

No Python files changed in 5DC, so `python -m py_compile`, Ruff, and pytest were not required.
