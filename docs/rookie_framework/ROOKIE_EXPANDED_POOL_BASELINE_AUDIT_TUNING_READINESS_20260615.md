# Rookie Expanded-Pool Baseline Audit / Tuning Readiness - 2026-06-15

## 1. Executive Verdict

This is an audit/readiness decision only. No tuning was run, no v2 board was created, and no production/app/promoted artifacts were touched.

Verdicts:

- Label quality: YELLOW
- Metric quality: GREEN
- Anti-cheat / leakage: GREEN
- Expanded baseline trust: YELLOW
- Tuning readiness: YELLOW
- Manual draft trust: YELLOW

The expanded baseline is useful enough to support a separate, tightly gated tuning prompt later, but it is not itself a current draft board or production ranking. The biggest audit finding is metric semantics: the previously reported global Top 12 / 24 / 36 metrics are useful rough diagnostics, but year-class Top-N metrics are the draft-realistic view because Tim drafts from one rookie class at a time.

## 2. Files and Exports Inspected

Primary inspected inputs:

- `local_exports/rookie_framework/historical_allowlist_qa_expanded_baseline_20260615/expanded_historical_labels_v2_20260615.csv`
- `local_exports/rookie_framework/historical_allowlist_qa_expanded_baseline_20260615/expanded_baseline_results_20260615.csv`
- `local_exports/rookie_framework/historical_allowlist_qa_expanded_baseline_20260615/expanded_baseline_year_position_summary_20260615.csv`
- `local_exports/rookie_framework/historical_allowlist_qa_expanded_baseline_20260615/expanded_baseline_top_misses_and_busts_20260615.csv`

New local-only exports:

- `metric_semantics_audit_20260615.csv`
- `year_class_baseline_metrics_20260615.csv`
- `position_baseline_metrics_20260615.csv`
- `top_missed_stars_diagnostic_20260615.csv`
- `high_ranked_busts_diagnostic_20260615.csv`
- `feature_family_hypotheses_20260615.csv`
- `tuning_readiness_decision_20260615.csv`
- `README_ROOKIE_EXPANDED_POOL_BASELINE_AUDIT_TUNING_READINESS_20260615.md`

## 3. Baseline Metric Semantics

Global pool Top-N:

- Star denominator: all 125 stars in the complete-window pool.
- Bust-rate denominator: selected Top-N rows from the entire complete-window pool.
- Draft realism: low to medium.
- Interpretation: useful for rough sorting diagnostics, not draft-realistic by itself.

Year-class Top-N:

- Star denominator: stars in that draft year, or stars in a period when aggregating per-year selections.
- Bust-rate denominator: selected Top-N rows within each draft class.
- Draft realism: high.
- Interpretation: primary metric family for rookie draft simulation and any later tuning gates.

Position Top-N:

- Star denominator: stars within QB/RB/WR/TE.
- Bust-rate denominator: selected Top-N rows within the position.
- Draft realism: medium.
- Interpretation: useful for 1QB discipline, TE strictness, and RB/WR balance.

Conclusion: the low global star capture rates are partly a metric-definition artifact. The year-class view shows the draft-capital/position baseline captures far more stars when evaluated as one rookie class at a time, but it also reveals a meaningful bust-avoidance problem in later historical classes.

## 4. Year-Class Metrics

Year-class Top 12 summary:

| Year | Rows | Stars | Stars Captured | Star Capture | Busts Selected | Bust Rate |
|---|---:|---:|---:|---:|---:|---:|
| 2010 | 77 | 9 | 5 | 0.556 | 0 | 0.000 |
| 2011 | 82 | 8 | 3 | 0.375 | 1 | 0.083 |
| 2012 | 77 | 10 | 4 | 0.400 | 1 | 0.083 |
| 2013 | 79 | 7 | 4 | 0.571 | 0 | 0.000 |
| 2014 | 76 | 10 | 4 | 0.400 | 0 | 0.000 |
| 2015 | 79 | 6 | 3 | 0.500 | 2 | 0.167 |
| 2016 | 75 | 7 | 3 | 0.429 | 0 | 0.000 |
| 2017 | 80 | 17 | 6 | 0.353 | 0 | 0.000 |
| 2018 | 81 | 7 | 5 | 0.714 | 0 | 0.000 |
| 2019 | 80 | 9 | 5 | 0.556 | 1 | 0.083 |
| 2020 | 78 | 8 | 4 | 0.500 | 1 | 0.083 |
| 2021 | 76 | 11 | 7 | 0.636 | 4 | 0.333 |
| 2022 | 79 | 7 | 2 | 0.286 | 4 | 0.333 |
| 2023 | 80 | 9 | 4 | 0.444 | 2 | 0.167 |

Period-level year-class selections:

| Period | Bucket | Selected | Stars | Stars Captured | Star Capture | Busts Selected | Bust Rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2010-2014 | Top 12 | 60 | 44 | 20 | 0.455 | 2 | 0.033 |
| 2010-2014 | Top 24 | 120 | 44 | 32 | 0.727 | 11 | 0.092 |
| 2010-2014 | Top 36 | 180 | 44 | 40 | 0.909 | 22 | 0.122 |
| 2015-2019 | Top 12 | 60 | 46 | 22 | 0.478 | 3 | 0.050 |
| 2015-2019 | Top 24 | 120 | 46 | 34 | 0.739 | 8 | 0.067 |
| 2015-2019 | Top 36 | 180 | 46 | 40 | 0.870 | 23 | 0.128 |
| 2020-2023 | Top 12 | 48 | 35 | 17 | 0.486 | 11 | 0.229 |
| 2020-2023 | Top 24 | 96 | 35 | 24 | 0.686 | 33 | 0.344 |
| 2020-2023 | Top 36 | 144 | 35 | 30 | 0.857 | 63 | 0.438 |
| 2010-2023 | Top 12 | 168 | 125 | 59 | 0.472 | 16 | 0.095 |
| 2010-2023 | Top 24 | 336 | 125 | 90 | 0.720 | 52 | 0.155 |
| 2010-2023 | Top 36 | 504 | 125 | 110 | 0.880 | 108 | 0.214 |

Diagnosis:

- Top 12 year-class star capture is usable but not dominant.
- Top 24 and Top 36 year-class views capture most stars, which supports tuning readiness.
- The 2020-2023 slice has much higher selected bust rates, so later tuning must explicitly validate bust avoidance and not just chase star capture.

## 5. Position Metrics

| Position | Rows | Stars | Top 12 Capture | Top 24 Capture | Top 36 Capture | Top 36 Bust Rate | Calibration Note |
|---|---:|---:|---:|---:|---:|---:|---|
| QB | 156 | 17 | 0.294 | 0.529 | 0.706 | 0.111 | 1QB devaluation appears meaningful but not empty |
| RB | 302 | 46 | 0.261 | 0.326 | 0.435 | 0.028 | acceptable baseline balance |
| WR | 431 | 37 | 0.189 | 0.243 | 0.351 | 0.111 | acceptable baseline balance, but upside features likely matter |
| TE | 210 | 25 | 0.200 | 0.480 | 0.520 | 0.083 | usable with continued caution |

Diagnosis:

- QB is devalued in a way that fits 1QB discipline, but QB evaluation is not empty.
- RB bust control is strong at the position level, but star capture is modest.
- WR capture is the weakest of the major fantasy positions, suggesting the baseline lacks target earning, separation, route, explosive play, and role-context feature families.
- TE capture is not broken, but any tuning should keep TE gates cautious.

## 6. Top Missed Stars

Top missed stars diagnostic rows exported: 30.

Classification counts:

- `true_model_miss`: 13
- `scoring_format_issue`: 12
- `position_calibration_issue`: 5

Examples from the diagnostic export, names used only for diagnosis:

- CeeDee Lamb, Josh Jacobs, Najee Harris, Brandin Cooks, Jaxon Smith-Njigba, Travis Etienne, Demaryius Thomas, Justin Jefferson, Zay Flowers, Dez Bryant, Calvin Ridley, Doug Martin.

General feature-family diagnosis:

- Draft-capital/position baseline misses too much WR/RB upside when the player is a later first-round or late-round-one profile rather than a very early pick.
- QB misses should be reviewed through 1QB scoring, not forced upward.
- TE misses should be reviewed through position-specific development and role-path gates.
- No player-specific boost is recommended or allowed.

## 7. High-Ranked Busts

High-ranked bust diagnostic rows exported: 2.

Classification counts:

- `draft_capital_trap`: 2

Names used only for diagnosis:

- Kevin White
- Jahan Dotson

General warning/gate diagnosis:

- The baseline can overtrust early draft capital when warning/gate evidence is not present.
- Later tuning should test general warning visibility and bust-gate feature families, not special-case historical busts.

## 8. Conservative / Upside Balance

The expanded baseline is metric-limited and somewhat conservative in the global view, but the year-class view shows it is not as conservative as the global Top-N rows imply.

Best description:

- Metric-limited: yes.
- Label-limited: partially, because 10 excluded rows and 160 partial rows remain.
- Too conservative: partly, especially for WR/RB upside outside the earliest picks.
- Too upside-heavy: not globally, but 2020-2023 year-class Top 24/36 bust rates are high enough that tuning must protect bust avoidance.
- Position-biased: not fatally, but WR upside and QB/TE calibration need separate holdout checks.
- Reasonably balanced: only as a baseline diagnostic, not as a tuned model.

## 9. Anti-Cheat / Leakage Audit

PASS - No player-specific tuning rules were added.

PASS - No `if player == ...` boost/penalty logic was added.

PASS - Names, IDs, schools, NFL teams, and draft years are used only for identity, display, grouping, QA, splitting, and deterministic diagnostics.

PASS - Outcome labels are used only for evaluation and diagnostics.

PASS - ADP/market/public rankings/projections/trade calculators are not used as private score or tuning inputs.

PASS - Draft-source future/career fields remain quarantined.

PASS - No probabilities, bands, hidden sort keys, or promoted artifacts were consumed.

PASS - No tuning script was executed.

PASS - No v2 board was created.

## 10. Tuning Readiness Decision

Tuning readiness: YELLOW.

It is safe to prepare a separate, explicitly approved tuning prompt, but tuning should not start automatically. The next tuning task must:

- Use year-class Top-N metrics as the primary draft-realistic objective.
- Keep 2024-2025 partial rows out of tuning.
- Use 2021-2022 or a broader pre-2023 slice for development and 2023 as a holdout, unless HQ approves another split.
- Preserve anti-cheat rules.
- Test feature-family weights/gates only.
- Report baseline-before, label-repair-before, and tuning-after metrics separately.
- Avoid player, team, school, class, or known-outcome special cases.

Recommended next prompt:

Run a rookie-only no-leakage expanded-pool tuning design pass. Do not tune yet. Define train/validation/holdout splits, eligible feature families, objective metrics, stop rules, and report templates for star capture, bust avoidance, warning calibration, and position calibration. Keep ADP/market display-only and exclude all names, IDs, teams, schools, draft years, outcomes, probabilities, bands, hidden sort keys, and promoted artifacts from scoring features.
