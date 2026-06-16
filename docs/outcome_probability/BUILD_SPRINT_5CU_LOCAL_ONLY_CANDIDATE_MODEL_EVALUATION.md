# Sprint 5CU: Local-Only Candidate Model Evaluation

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_LOCAL_ONLY_CANDIDATE_MODEL_EVALUATION`

Sprint type: `HISTORICAL_FOLD_EVALUATION_NO_PRODUCTION_NO_DISPLAY`

## 1. Scope

Sprint 5CU ran local-only historical candidate model evaluation for the 5CS-approved candidate heads using the committed 5CT harness. This sprint trained and evaluated only inside historical rolling folds. It did not run current-player inference, create current-player probabilities, create production model artifacts, serialize model files, create app-readable outputs, create exact display percentages, create coarse bands, wire app display, alter rankings/sorting, create hidden sort keys, create promoted artifacts, touch rookie files, edit or commit `data/`, stage or commit `local_exports/`, push, or deploy.

## 2. Files And Local-Only Outputs

Tracked file created:

- `docs/outcome_probability/BUILD_SPRINT_5CU_LOCAL_ONLY_CANDIDATE_MODEL_EVALUATION.md`

Tracked script used:

- `scripts/outcome_probability/run_sprint_5ct_phase5_candidate_modeling_harness.py`

Local-only evidence created:

`local_exports/outcome_probability/sprint_5cu_phase5_local_candidate_model_evaluation/`

Local-only files created:

- `aggregate_metrics_by_head_fold_method.csv`
- `head_candidate_verdicts.csv`
- `feature_quarantine_audit.csv`
- `candidate_logistic_coefficients.csv`
- `metadata.json`
- `README.md`

No row-level prediction export was created.

## 3. Heads Evaluated

Evaluated approved heads:

- `qb_t12`
- `qb_t18`
- `qb_t24`
- `rb_t12`
- `rb_t24`
- `wr_t12`
- `wr_t24`
- `wr_t36`
- `te_t12`
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

5CU used deterministic rolling historical folds:

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

| Head | Canonical head | Position | Mean AUC | Mean Brier | Base Brier | Mean log loss | Base log loss | Thin calibration bins | Verdict |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `qb_t12` | `same_year_qb_t12` | QB | 0.863968 | 0.122189 | 0.168098 | 0.378853 | 0.519141 | 6 | `candidate_accept` |
| `qb_t18` | `same_year_qb_t18` | QB | 0.867506 | 0.140331 | 0.217129 | 0.422201 | 0.625984 | 11 | `candidate_caution` |
| `qb_t24` | `same_year_qb_t24` | QB | 0.888251 | 0.133844 | 0.243236 | 0.419866 | 0.679627 | 9 | `candidate_caution` |
| `rb_t12` | `same_year_rb_t12` | RB | 0.857595 | 0.074577 | 0.091526 | 0.271993 | 0.329510 | 7 | `candidate_accept` |
| `rb_t24` | `same_year_rb_t24` | RB | 0.833113 | 0.120540 | 0.161677 | 0.387880 | 0.504422 | 7 | `candidate_caution` |
| `wr_t12` | `same_year_wr_t12` | WR | 0.911960 | 0.057528 | 0.072386 | 0.219716 | 0.275268 | 4 | `candidate_accept` |
| `wr_t24` | `same_year_wr_t24` | WR | 0.871147 | 0.091423 | 0.127764 | 0.310583 | 0.423411 | 6 | `candidate_accept` |
| `wr_t36` | `same_year_wr_t36` | WR | 0.861316 | 0.116724 | 0.173047 | 0.376227 | 0.530253 | 4 | `candidate_accept` |
| `te_t12` | `same_year_te_t12` | TE | 0.881903 | 0.083483 | 0.116241 | 0.289116 | 0.394461 | 8 | `candidate_accept` |
| `te_t18` | `same_year_te_t18` | TE | 0.858787 | 0.106301 | 0.151129 | 0.350109 | 0.479938 | 11 | `candidate_caution` |
| `te_t24` | `same_year_te_t24` | TE | 0.853641 | 0.125014 | 0.185089 | 0.395475 | 0.557124 | 10 | `candidate_caution` |

Useful conservative candidate set remains:

- `qb_t12`
- `rb_t12`
- `wr_t12`
- `wr_t24`
- `wr_t36`
- `te_t12`

Caution candidates for later audit:

- `qb_t18`
- `qb_t24`
- `rb_t24`
- `te_t18`
- `te_t24`

Rejected or insufficient-support candidates: none.

## 6. Support And Baseline Summary

All evaluated candidate heads had four historical rolling folds. Each candidate logistic model improved mean Brier and mean log loss relative to the training-fold base-rate baseline.

The candidate verdict does not approve production or display. It only identifies which heads are strong enough for a candidate-model audit.

## 7. Quarantine And Guardrail Results

Feature quarantine result: pass.

Forbidden feature failures: 0.

The harness used only approved source-safe prior completed-season features and did not use target-year outcomes, current-player inputs, fantasy totals, EPA, WOPR/RACR/PACR/Dakota, target-share fields, ADP, projections, public rankings, market/trade values, RotoWire values, prior fantasy draft history, or legacy `private_score`.

Output quarantine result: pass.

5CU metadata confirms:

- row-level predictions exported: false
- current-player inference performed: false
- app-readable outputs created: false
- serialized model artifacts created: false
- production model artifacts created: false
- exact display percentages created: false
- coarse display bands created: false
- app wiring created: false
- rankings/sorting created: false
- hidden sort keys created: false
- promoted artifacts created: false

## 8. Verdict

5CU verdict: GREEN.

Evaluation ran for approved heads only. Deferred and blocked heads remained excluded. No leakage, current-player output, app-readable output, rookie contamination, production artifact, ranking, sorting, hidden-key, or promotion risk appeared.

5CV is approved to run next as an audit of candidate calibration, leakage, support, and football sanity.

## 9. Checks

Checks run:

- `python scripts\outcome_probability\run_sprint_5ct_phase5_candidate_modeling_harness.py --mode evaluate --heads approved --output-dir local_exports\outcome_probability\sprint_5cu_phase5_local_candidate_model_evaluation` passed
- `python -m py_compile scripts\outcome_probability\run_sprint_5ct_phase5_candidate_modeling_harness.py` passed
- `git diff --check` passed

Ruff and pytest were not required and no package installation was performed.
