# Sprint 5CO: Local-Only Aggregate Shadow Model Evaluation

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_LOCAL_ONLY_AGGREGATE_SHADOW_EVALUATION`

Sprint type: `LOCAL_SHADOW_EVALUATION_NO_PRODUCTION_NO_DISPLAY`

## 1. Scope

Sprint 5CO ran local-only aggregate shadow threshold model evaluation for the 14 Sprint 5CN-approved heads. This sprint produced aggregate diagnostics only. It did not create row-level or player-level predicted probability exports, current-player probabilities, exact display percentages, coarse display bands, app-readable outputs, app wiring, rankings/sorting, hidden sort keys, production model artifacts, pickled promoted models, rookie files, `data/` edits, `local_exports/` commits, push, or deploy.

## 2. Files And Local-Only Outputs

Tracked files created:

- `docs/outcome_probability/BUILD_SPRINT_5CO_LOCAL_ONLY_AGGREGATE_SHADOW_MODEL_EVALUATION.md`
- `scripts/outcome_probability/build_sprint_5co_local_only_aggregate_shadow_model_evaluation.py`

Created local-only export:

`local_exports/outcome_probability/sprint_5co_local_only_aggregate_shadow_model_evaluation/`

Created local-only files:

| File | Purpose | App-readable? |
| --- | --- | --- |
| `metadata_sprint_5co.json` | verdict, method counts, output quarantine flags | no |
| `aggregate_metrics_by_head_fold.csv` | aggregate metrics by head, fold, and method | no |
| `head_metric_summary.csv` | aggregate head-level shadow metric summary | no |
| `feature_quarantine_audit.csv` | 5CN allowlist and forbidden-term check | no |
| `logistic_coefficients_by_head_fold.csv` | local-only aggregate coefficient diagnostics | no |
| `README_SPRINT_5CO.md` | local package summary | no |

No row-level or player-level prediction file was written.

## 3. Heads Evaluated

Evaluated heads:

- `same_year_qb_t12`
- `same_year_qb_t18`
- `same_year_qb_t24`
- `same_year_rb_t12`
- `same_year_rb_t24`
- `same_year_rb_t36`
- `same_year_rb_t48`
- `same_year_wr_t12`
- `same_year_wr_t24`
- `same_year_wr_t36`
- `same_year_wr_t48`
- `same_year_te_t12`
- `same_year_te_t18`
- `same_year_te_t24`

Weak 5CN heads not evaluated:

- `same_year_qb_t6`
- `same_year_rb_t6`
- `same_year_wr_t6`
- `same_year_te_t3`
- `same_year_te_t6`

## 4. Split Design

5CO used the 5CN-approved rolling holdout split:

| Fold | Training target seasons | Holdout target season |
| --- | --- | ---: |
| 1 | 2010-2015 | 2016 |
| 2 | 2010-2016 | 2017 |
| 3 | 2010-2017 | 2018 |
| 4 | 2010-2018 | 2019 |

No random split was used.

## 5. Methods

Methods evaluated:

- `base_rate_train_fold`: training-fold base-rate baseline
- `prior_rank_score`: source-safe prior NWR finish-rank score baseline
- `prior_ppg_score`: source-safe prior NWR PPG score baseline
- `logistic_low_complexity`: low-complexity in-script logistic model

The script did not perform broad hyperparameter search and did not persist model objects.

## 6. Aggregate Shadow Metric Summary

The table below summarizes the local-only logistic shadow diagnostics across the four rolling folds:

| Head | Position | Folds | Mean AUC | Mean Brier | Mean log loss |
| --- | --- | ---: | ---: | ---: | ---: |
| `same_year_qb_t12` | QB | 4 | 0.864458 | 0.123458 | 0.383753 |
| `same_year_qb_t18` | QB | 4 | 0.866436 | 0.141340 | 0.425524 |
| `same_year_qb_t24` | QB | 4 | 0.886623 | 0.134615 | 0.421872 |
| `same_year_rb_t12` | RB | 4 | 0.856565 | 0.075875 | 0.278369 |
| `same_year_rb_t24` | RB | 4 | 0.833380 | 0.121243 | 0.390898 |
| `same_year_rb_t36` | RB | 4 | 0.811877 | 0.155920 | 0.478715 |
| `same_year_rb_t48` | RB | 4 | 0.837468 | 0.160292 | 0.493783 |
| `same_year_wr_t12` | WR | 4 | 0.911838 | 0.058918 | 0.227622 |
| `same_year_wr_t24` | WR | 4 | 0.870802 | 0.092451 | 0.315514 |
| `same_year_wr_t36` | WR | 4 | 0.861176 | 0.117421 | 0.379114 |
| `same_year_wr_t48` | WR | 4 | 0.839714 | 0.142252 | 0.442820 |
| `same_year_te_t12` | TE | 4 | 0.881597 | 0.084521 | 0.294565 |
| `same_year_te_t18` | TE | 4 | 0.859027 | 0.107078 | 0.353802 |
| `same_year_te_t24` | TE | 4 | 0.853827 | 0.125477 | 0.397560 |

These values are internal aggregate diagnostics only. They are not player-facing percentages, probabilities, bands, or release claims.

## 7. Feature Quarantine Audit

5CO used only the 5CN-approved feature allowlist:

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

Forbidden feature failures: 0.

The script did not use fantasy totals, EPA, WOPR/RACR/PACR/Dakota, target-share style fields, market ranks, ADP, projections, public rankings, consensus, trade values, RotoWire values/outlooks/projections, prior fantasy draft history, legacy `private_score`, target-year outcomes as features, or same-season final stats as preseason features.

## 8. Output Quarantine

Output quarantine result: pass.

5CO wrote only local-only aggregate diagnostics under:

`local_exports/outcome_probability/sprint_5co_local_only_aggregate_shadow_model_evaluation/`

5CO did not write:

- row-level/player-level predicted probability CSVs
- current-player probabilities
- exact display percentages
- coarse display bands
- app-readable probability/band/status outputs
- production model artifacts
- pickled promoted models
- ranking/sorting outputs
- hidden sort keys
- app wiring

## 9. Verdict

5CO verdict: GREEN.

Aggregate metrics are available for all 14 5CN-approved heads. The local-only outputs remain quarantined and do not create release/display artifacts.

5CP is approved to run next as an audit of backtest quality, calibration, sanity, and leakage risk.

## 10. Release Stance

Model production remains blocked.

Current-player probabilities remain blocked.

Exact display percentages remain blocked.

Coarse display bands remain blocked.

App wiring remains blocked.

Rankings/sorting and hidden sort keys remain blocked.

Promoted artifacts remain blocked.

No app-readable probability, band, or status output was created.

## 11. Checks

Checks run:

- `python scripts\outcome_probability\build_sprint_5co_local_only_aggregate_shadow_model_evaluation.py` passed
- `python -m py_compile scripts\outcome_probability\build_sprint_5co_local_only_aggregate_shadow_model_evaluation.py` passed
- `git diff --check` passed

Ruff was not run because it is optional and no package installation is allowed. Pytest was not required because no production code or tests changed.
