# Sprint 5DA: Phase 6 Local-Only Production-Candidate Modeling

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_LOCAL_ONLY_PRODUCTION_CANDIDATE_MODELING`

Sprint type: `HISTORICAL_FOLD_MODELING_NO_CURRENT_INFERENCE_NO_RELEASE`

## 1. Scope

Sprint 5DA ran the committed 5CZ local-only production-candidate harness for the six 5CY-approved Phase 6 heads. The run used historical 2010-2019 feature/label rows only and wrote quarantined aggregate evidence under `local_exports/`.

This sprint did not run current-player inference, create current-player probabilities, create exact display percentages, create coarse display bands, create app-readable outputs, wire app display, alter rankings/sorting, create hidden sort keys, create promoted artifacts, touch rookie files, edit or commit `data/`, stage or commit `local_exports/`, push, or deploy.

## 2. Files And Local-Only Outputs

Tracked files:

- `docs/outcome_probability/BUILD_SPRINT_5DA_PHASE_6_LOCAL_ONLY_PRODUCTION_CANDIDATE_MODELING.md`
- `scripts/outcome_probability/run_sprint_5da_phase6_local_only_production_candidate_modeling.py`

Committed harness used:

- `scripts/outcome_probability/build_sprint_5cz_phase6_production_candidate_harness.py`

Local-only evidence:

`local_exports/outcome_probability/sprint_5da_phase6_local_only_production_candidate_modeling/`

Local-only files created:

- `aggregate_metrics_by_head_fold_method.csv`
- `candidate_logistic_coefficients.csv`
- `feature_quarantine_audit.csv`
- `head_candidate_verdicts.csv`
- `metadata.json`
- `README.md`

The local-only evidence is not app-readable and is not staged or committed.

## 3. Heads Run

Eligible Phase 6 heads run:

- `qb_t12`
- `rb_t12`
- `wr_t12`
- `wr_t24`
- `wr_t36`
- `te_t12`

Caution heads excluded:

- `qb_t18`
- `qb_t24`
- `rb_t24`
- `te_t18`
- `te_t24`

Deferred heads excluded:

- `rb_t36`
- `rb_t48`
- `wr_t48`

Blocked heads excluded:

- `qb_t6`
- `rb_t6`
- `wr_t6`
- `te_t3`
- `te_t6`

## 4. Evaluation Strategy

5DA used the deterministic rolling historical folds inherited from the 5CZ harness:

| Fold | Training target seasons | Holdout target season |
| --- | --- | ---: |
| 1 | 2010-2015 | 2016 |
| 2 | 2010-2016 | 2017 |
| 3 | 2010-2017 | 2018 |
| 4 | 2010-2018 | 2019 |

Methods evaluated:

- training-fold base-rate baseline
- source-safe prior-rank score baseline
- source-safe prior-PPG score baseline
- low-complexity candidate logistic model

No broad hyperparameter search was performed.

## 5. Candidate Verdicts And Metrics

| Head | Canonical head | Position | Mean AUC | Mean Brier | Base Brier | Mean log loss | Base log loss | Thin calibration bins | Preliminary tier |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `qb_t12` | `same_year_qb_t12` | QB | 0.863968 | 0.122189 | 0.168098 | 0.378853 | 0.519141 | 6 | accepted for 5DB audit |
| `rb_t12` | `same_year_rb_t12` | RB | 0.857595 | 0.074577 | 0.091526 | 0.271993 | 0.329510 | 7 | accepted for 5DB audit |
| `wr_t12` | `same_year_wr_t12` | WR | 0.911960 | 0.057528 | 0.072386 | 0.219716 | 0.275268 | 4 | accepted for 5DB audit |
| `wr_t24` | `same_year_wr_t24` | WR | 0.871147 | 0.091423 | 0.127764 | 0.310583 | 0.423411 | 6 | accepted for 5DB audit |
| `wr_t36` | `same_year_wr_t36` | WR | 0.861316 | 0.116724 | 0.173047 | 0.376227 | 0.530253 | 4 | accepted for 5DB audit |
| `te_t12` | `same_year_te_t12` | TE | 0.881903 | 0.083483 | 0.116241 | 0.289116 | 0.394461 | 8 | accepted for 5DB audit |

All six heads improved mean Brier and mean log loss versus the training-fold base-rate baseline. All six heads remain preliminary until 5DB audits calibration, leakage, sanity, support, and quarantine.

## 6. Support And Calibration Watch Items

Minimum fold support and maximum fold calibration gap from the candidate logistic method:

| Head | Min train rows | Min train positives | Min holdout rows | Min holdout positives | Max calibration gap |
| --- | ---: | ---: | ---: | ---: | ---: |
| `qb_t12` | 342 | 67 | 50 | 11 | 0.646958 |
| `rb_t12` | 583 | 65 | 94 | 9 | 0.529152 |
| `wr_t12` | 847 | 69 | 141 | 10 | 0.506245 |
| `wr_t24` | 847 | 133 | 141 | 20 | 0.210736 |
| `wr_t36` | 847 | 200 | 141 | 31 | 0.157622 |
| `te_t12` | 491 | 68 | 81 | 11 | 0.303062 |

The calibration-gap rows are local audit evidence only and do not approve display probabilities or bands. 5DB must decide whether these heads remain accepted, become caution, or are deferred.

## 7. Feature And Leakage Controls

Feature quarantine result: pass.

The feature audit used only:

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

Forbidden-field scan result: pass.

No target-season/future features, display fields, ADP, market values, trade values, RotoWire rankings/projections/outlooks/values, public rankings, projections, consensus, prior fantasy draft history, legacy `private_score`, fantasy totals, EPA, WOPR/RACR/PACR/Dakota, target-share fields, or same-season target stats were used as features.

## 8. Quarantine Metadata

5DA metadata confirms:

- `output_scope=internal_only_not_app_readable`
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

## 9. Gate Verdict

5DA verdict: GREEN.

The run is historical-only, quarantined, no current-player inference occurred, outputs are aggregate/local-only, and each preliminary accepted head has enough metrics for 5DB audit. Sprint 5DB may proceed as an audit of the 5DA local-only evidence.

## 10. Checks

Checks run:

- repo/path/branch/status/log preflight passed
- `python scripts\outcome_probability\run_sprint_5da_phase6_local_only_production_candidate_modeling.py` passed
- `python -m py_compile scripts\outcome_probability\run_sprint_5da_phase6_local_only_production_candidate_modeling.py` passed
- `python -m py_compile scripts\outcome_probability\build_sprint_5cz_phase6_production_candidate_harness.py` passed
- `git diff --check` passed

Ruff and pytest were not required and no package installation was performed.
