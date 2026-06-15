# Sprint 5CP: Backtest Calibration Sanity Audit

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_INTERNAL_BACKTEST_AUDIT_HUMAN_REVIEW_READY`

Sprint type: `AGGREGATE_AUDIT_NO_PRODUCTION_NO_DISPLAY`

## 1. Scope

Sprint 5CP audited the Sprint 5CO local-only aggregate shadow threshold model evaluation. This sprint analyzed aggregate outputs only. It did not train new models, export row-level or player-level probabilities, create current-player probabilities, create exact display percentages, create coarse display bands, create app-readable files, wire app display, alter rankings/sorting, create hidden sort keys, touch rookie files, edit `data/`, commit `local_exports/`, create production model artifacts, push, or deploy.

## 2. Audited Sources

5CP reviewed:

- `docs/outcome_probability/BUILD_SPRINT_5CN_LOCAL_SHADOW_MODEL_PREFLIGHT_DESIGN_GATE.md`
- `docs/outcome_probability/BUILD_SPRINT_5CO_LOCAL_ONLY_AGGREGATE_SHADOW_MODEL_EVALUATION.md`
- `scripts/outcome_probability/build_sprint_5co_local_only_aggregate_shadow_model_evaluation.py`
- `local_exports/outcome_probability/sprint_5co_local_only_aggregate_shadow_model_evaluation/`

5CO outputs remain local-only and aggregate-only.

## 3. Quality Tiers

Viable heads for continued human review:

- `same_year_qb_t12`
- `same_year_qb_t18`
- `same_year_qb_t24`
- `same_year_rb_t12`
- `same_year_rb_t24`
- `same_year_wr_t12`
- `same_year_wr_t24`
- `same_year_wr_t36`
- `same_year_te_t12`
- `same_year_te_t18`
- `same_year_te_t24`

Weak heads requiring caution in human review:

- `same_year_rb_t36`
- `same_year_rb_t48`
- `same_year_wr_t48`

Blocked/not evaluated heads:

- `same_year_qb_t6`
- `same_year_rb_t6`
- `same_year_wr_t6`
- `same_year_te_t3`
- `same_year_te_t6`

No evaluated head is approved for display or release.

## 4. Aggregate Backtest Summary

The table below summarizes the 5CO logistic aggregate diagnostics and base-rate comparison across rolling holdout folds:

| Head | Mean AUC | Mean Brier | Base Brier | Mean log loss | Base log loss | Thin calibration bins |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `same_year_qb_t12` | 0.864458 | 0.123458 | 0.168098 | 0.383753 | 0.519141 | 5 |
| `same_year_qb_t18` | 0.866436 | 0.141340 | 0.217129 | 0.425524 | 0.625984 | 12 |
| `same_year_qb_t24` | 0.886623 | 0.134615 | 0.243236 | 0.421872 | 0.679627 | 9 |
| `same_year_rb_t12` | 0.856565 | 0.075875 | 0.091526 | 0.278369 | 0.329510 | 7 |
| `same_year_rb_t24` | 0.833380 | 0.121243 | 0.161677 | 0.390898 | 0.504422 | 7 |
| `same_year_rb_t36` | 0.811877 | 0.155920 | 0.210721 | 0.478715 | 0.612426 | 5 |
| `same_year_rb_t48` | 0.837468 | 0.160292 | 0.239091 | 0.493783 | 0.671190 | 3 |
| `same_year_wr_t12` | 0.911838 | 0.058918 | 0.072386 | 0.227622 | 0.275268 | 4 |
| `same_year_wr_t24` | 0.870802 | 0.092451 | 0.127764 | 0.315514 | 0.423411 | 5 |
| `same_year_wr_t36` | 0.861176 | 0.117421 | 0.173047 | 0.379114 | 0.530253 | 4 |
| `same_year_wr_t48` | 0.839714 | 0.142252 | 0.208458 | 0.442820 | 0.607619 | 2 |
| `same_year_te_t12` | 0.881597 | 0.084521 | 0.116241 | 0.294565 | 0.394461 | 8 |
| `same_year_te_t18` | 0.859027 | 0.107078 | 0.151129 | 0.353802 | 0.479938 | 11 |
| `same_year_te_t24` | 0.853827 | 0.125477 | 0.185089 | 0.397560 | 0.557124 | 10 |

All evaluated heads improved aggregate Brier and log loss versus the training-fold base-rate baseline. This is encouraging for internal review, but it is not release approval.

## 5. Calibration And Stability Notes

Calibration audit result: GREEN for continued human review, with constraints.

Important constraints:

- Calibration bins are often thin because holdout seasons are single-season folds.
- QB Top 18, QB Top 24, TE Top 18, and TE Top 24 have several thin calibration bins and need careful review.
- RB Top 36 and RB Top 48 have weaker aggregate AUC and higher Brier than the stronger heads.
- WR Top 48 is informative but weaker than WR Top 12/24/36.

No head is calibrated well enough for exact percentages or coarse bands.

## 6. Baseline Comparison

Baseline comparison result: pass for internal review.

The low-complexity logistic shadow model improves aggregate Brier and log loss versus the base-rate baseline for every evaluated head. Prior-rank and prior-PPG score baselines were evaluated in the local-only aggregate metrics as source-safe directional baselines.

5CP does not claim production superiority or release readiness.

## 7. Directional Sanity

Directional sanity result: pass for continued review.

The evaluated feature set is driven by completed prior-season games, prior production, first downs, yards, prior NWR finish rank, and prior NWR PPG. Those features are directionally plausible for future threshold support. The audit did not identify a systematic sign that stronger prior production reduces modeled outcome likelihood across the aggregate summaries.

5CP recommends a later human review of coefficient diagnostics before any Phase 5 modeling proposal is run.

## 8. Leakage And Output Audit

Leakage audit result: pass.

Forbidden feature failures in 5CO: 0.

5CO used only 5CN-approved prior completed-season features and did not use fantasy totals, EPA, WOPR/RACR/PACR/Dakota, target-share style fields, market ranks, ADP, projections, public rankings, consensus, trade values, RotoWire values/outlooks/projections, prior fantasy draft history, legacy `private_score`, target-year labels as features, or same-season final stats as preseason features.

Output audit result: pass.

5CO metadata confirms:

- row-level predictions exported: false
- current-player probabilities created: false
- exact display percentages created: false
- coarse display bands created: false
- app-readable outputs created: false
- production model artifacts created: false
- model pickles created: false
- app wiring created: false
- rankings/sorting created: false
- hidden sort keys created: false
- promoted artifacts created: false

## 9. Verdict

5CP verdict: GREEN.

At least one meaningful subset of heads is quality-acceptable for continued human review. Weak heads and blocked/not-evaluated heads are clearly separated. No leakage, app-output, provenance, rookie, ranking, or productionization violation was found.

5CQ is approved to run next as a human review packet with no app output.

## 10. Release Stance

Production model artifacts remain blocked.

Current-player probabilities remain blocked.

Exact display percentages remain blocked.

Coarse display bands remain blocked.

App wiring remains blocked.

Rankings/sorting and hidden sort keys remain blocked.

Promoted artifacts remain blocked.

No app-readable probability, band, or status output was created.

## 11. Checks

Checks run:

- local aggregate 5CO output audit completed
- `git diff --check` passed

No Python files changed in 5CP, so `python -m py_compile`, Ruff, and pytest are not required.
