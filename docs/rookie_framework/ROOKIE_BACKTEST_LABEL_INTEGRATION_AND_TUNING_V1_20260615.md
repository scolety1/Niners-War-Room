# Rookie Backtest Label Integration and Tuning v1 - 2026-06-15

## Executive Verdict

Backtest readiness verdict: GREEN.

Manual draft ranking trust verdict after backtest: YELLOW.

The historical outcome label package now joins into the rookie backtest scaffold and produces repeatable local-only baseline metrics on 2021-2023 complete-window rows. Tuning experiments ran only after the label join was GREEN. The tuning outputs are experimental and manual-use-only; they do not replace the official v1 board and do not create production rankings, private scores, app outputs, probabilities, bands, hidden sort keys, or promoted artifacts.

## Isolation Result

This work stayed in the Rookie lane only.

No Outcome HQ files, outcome probability files, outcome columns, veteran files, production rankings, app or Streamlit files, probabilities, bands, hidden sort keys, promoted artifacts, or deployment flows were touched.

`data/` and `local_exports/` remain uncommitted.

## Files Changed

- `scripts/rookie_framework/backtest_rookie_ranking_model_v01.py`
- `scripts/rookie_framework/tune_rookie_ranking_model_v01.py`
- `tests/test_rookie_backtest_framework_v01.py`
- `tests/test_rookie_tuning_loop_v01.py`
- `docs/rookie_framework/ROOKIE_BACKTEST_LABEL_INTEGRATION_AND_TUNING_V1_20260615.md`

## Local-Only Exports

Export directory:

`local_exports/rookie_framework/backtest_label_integration_tuning_v1_20260615/`

Exports created:

- `rookie_backtest_join_audit_20260615.csv`
- `rookie_baseline_scored_rows_20260615.csv`
- `rookie_baseline_backtest_metrics_20260615.csv`
- `rookie_baseline_top_misses_20260615.csv`
- `rookie_warning_calibration_20260615.csv`
- `rookie_position_calibration_20260615.csv`
- `rookie_tuning_experiment_results_20260615.csv`
- `README_ROOKIE_BACKTEST_LABEL_INTEGRATION_AND_TUNING_V1_20260615.md`
- `README_ROOKIE_TUNING_LOOP_V1_20260615.md`

Legacy compatibility exports were also regenerated under local-only paths:

- `local_exports/rookie_framework/historical_backtest_v1_20260615/`
- `local_exports/rookie_framework/tuning_loop_v1_20260615/`

## Label Join Coverage

Join key: `historical_prospect_key`.

Overall join:

- Rows attempted: 395
- Rows joined: 395
- Rows unjoined: 0
- Duplicate feature keys: 0
- Duplicate label keys: 0
- Missing identity rows: 0
- Label leakage columns in feature input: 0
- Probability/band leakage columns: 0
- Market context rows: 0
- Join status: GREEN

Class-year join:

| Year | Attempted | Joined | Complete-window rows | Partial rows | Status |
|---|---:|---:|---:|---:|---|
| 2021 | 76 | 76 | 76 | 0 | GREEN |
| 2022 | 79 | 79 | 79 | 0 | GREEN |
| 2023 | 80 | 80 | 80 | 0 | GREEN |
| 2024 | 76 | 76 | 0 | 76 | YELLOW_PARTIAL_LABELS |
| 2025 | 84 | 84 | 0 | 84 | YELLOW_PARTIAL_LABELS |

Only 2021-2023 complete-window rows were used for the frozen baseline and tuning experiments. 2024-2025 remain report-only/holdout because future first-three-year seasons are unavailable.

## Frozen Baseline Results

Baseline row count: 235 complete-window rows.

Overall baseline buckets:

| Bucket | Stars captured | Star capture rate | Bust count | Bust rate | Avg first-three points |
|---|---:|---:|---:|---:|---:|
| Top 6 | 3 / 27 | 0.111 | 1 | 0.167 | 366.944 |
| Top 12 | 5 / 27 | 0.185 | 3 | 0.250 | 351.230 |
| Top 24 | 9 / 27 | 0.333 | 6 | 0.250 | 359.404 |
| Top 36 | 10 / 27 | 0.370 | 13 | 0.361 | 318.019 |

Year-by-year top-24 results:

| Year | Stars captured | Star capture rate | Bust count | Bust rate |
|---|---:|---:|---:|---:|
| 2021 | 8 / 11 | 0.727 | 13 | 0.542 |
| 2022 | 4 / 7 | 0.571 | 11 | 0.458 |
| 2023 | 6 / 9 | 0.667 | 10 | 0.417 |

The baseline finds meaningful stars by top 24/top 36 within class years, but the early buckets still miss too many stars and carry too many busts for full manual trust.

## Warning Calibration

| Warning bucket | Rows | Star rate | Bust rate | Avg first-three points |
|---|---:|---:|---:|---:|
| Heavy | 66 | 0.106 | 0.773 | 126.532 |
| Low | 164 | 0.122 | 0.689 | 165.827 |
| None | 5 | 0.000 | 1.000 | 1.007 |

Warnings are directionally useful, but they are not strong enough alone to separate high-upside exceptions from broad bust risk. Warning visibility remains mandatory.

## Position Calibration

| Position | Rows | Star rate | Bust rate | Avg first-three points |
|---|---:|---:|---:|---:|
| QB | 33 | 0.030 | 0.788 | 179.957 |
| RB | 61 | 0.180 | 0.639 | 194.037 |
| TE | 46 | 0.130 | 0.804 | 87.739 |
| WR | 95 | 0.095 | 0.705 | 144.642 |

The 1QB devaluation is directionally supported. RBs show the best star rate in this scoring setup. TEs remain volatile and need exception handling rather than blanket promotion.

## Top Miss Themes

High-ranked bust examples included early WR misses such as Jahan Dotson, John Metchie III, Treylon Burks, Skyy Moore, Tyquan Thornton, Kadarius Toney, Rashod Bateman, and Terrace Marshall Jr.

Low-ranked star misses included Rachaad White, Devon Achane, Jaxon Smith-Njigba, Kyle Pitts, Trey McBride, Ja'Marr Chase, Sam LaPorta, Jaylen Waddle, and Amon-Ra St. Brown.

One caution: some assumed-zero label rows may still hide alias/stat matching quality issues. Nathaniel Dell appears as a high-ranked bust in the baseline miss export, which likely needs label alias review before treating that miss as a true model failure.

## Tuning Status

Tuning ran because the complete-window join was GREEN.

Split:

- Train/tune: 2021-2022
- Validate: 2023
- Hold out/report only: 2024-2025

Candidates evaluated:

- `baseline_v1`
- `star_capture_plus`
- `bust_avoidance_plus`
- `non_ppr_role_plus`
- `qb_devalue_plus`

Validation summary:

| Candidate | 2023 top-12 star capture | 2023 top-24 bust rate | 2023 top-36 bust rate | Low-ranked star misses | Production allowed |
|---|---:|---:|---:|---:|---|
| baseline_v1 | 0.333 | 0.417 | 0.528 | 2 | no |
| star_capture_plus | 0.333 | 0.375 | 0.500 | 2 | no |
| bust_avoidance_plus | 0.333 | 0.417 | 0.528 | 2 | no |
| non_ppr_role_plus | 0.333 | 0.417 | 0.528 | 2 | no |
| qb_devalue_plus | 0.333 | 0.417 | 0.528 | 2 | no |

`star_capture_plus` improved validation bust rates without reducing top-12 star capture or increasing low-ranked star misses. It is not promoted. It is a candidate lesson only.

No v2 candidate board was created because the safe result is a candidate-weight lesson, not a current draft-board replacement.

## ADP and Market Overlay Isolation

No local admitted player-level ADP or market source was present for this backtest run.

Market context rows in the historical feature matrix: 0.

ADP/market remains display-only and was not used in:

- frozen baseline rank score
- tuning score
- star upside index
- bust risk index
- warning penalty
- any private quality score

## Backtest Readiness

Backtest readiness is GREEN for repeatable local historical evaluation on 2021-2023 complete-window rows.

The backtest should remain local-only until the label caveats and calibration warnings are reviewed.

## Manual Draft Ranking Trust

Manual draft ranking trust is YELLOW.

Reasons:

- Label integration is clean and repeatable.
- Baseline star capture is useful but not strong enough in early global buckets.
- Top-24/top-36 class-year star capture is promising.
- Bust rates remain too high in top-24/top-36 class-year buckets.
- Warning calibration is directionally useful but not sufficient.
- Historical alias/assumed-zero quality issues need review before interpreting all misses as model errors.
- Tuning produced a promising candidate lesson but no approved v2 board.

Tim can use the current rookie board as an advisory/manual review board, but not as a fully trusted final ranking or production/app ranking.

## Validation Commands

- `git status --short`
- `git branch --show-current`
- `git log --oneline -10`
- `git diff --check`
- `python scripts/rookie_framework/build_rookie_historical_outcome_labels_v1.py`
- `python scripts/rookie_framework/backtest_rookie_ranking_model_v01.py`
- `python scripts/rookie_framework/tune_rookie_ranking_model_v01.py`
- `python -m py_compile scripts/rookie_framework/backtest_rookie_ranking_model_v01.py scripts/rookie_framework/tune_rookie_ranking_model_v01.py`
- `python scripts/rookie_framework/build_rookie_review_board_v03.py --strict`
- `python scripts/rookie_framework/build_rookie_shadow_ranking_v03.py --strict`
- `python scripts/rookie_framework/build_rookie_production_candidate_v03.py --strict`
- `python scripts/rookie_framework/build_rookie_analyzer_v03.py --strict`
- `python scripts/rookie_framework/build_rookie_draft_day_simulation_v03.py --strict`
- `python scripts/rookie_framework/build_rookie_draft_ranking_v01.py`
- direct rookie framework harnesses
- `python -m pytest tests/test_rookie_backtest_framework_v01.py tests/test_rookie_tuning_loop_v01.py -q`

Pytest is unavailable in the local environment: `No module named pytest`.

## Remaining Blockers

- Review and repair any historical label alias issues, especially likely alias/stat mismatches in assumed-zero rows.
- Decide whether `star_capture_plus` deserves a separate candidate-board proposal.
- Add better treatment for WR early-career breakout profiles that were buried in baseline replay.
- Add stronger high-ranked bust avoidance for early WR profiles.
- Keep 2024-2025 out of tuning until complete outcome windows exist or a separate year1/year2 objective is approved.
- Do not promote anything into app/production until Tim/HQ approves a separate production implementation path.

## Exact Next Safe Step

Run a rookie-only historical label quality/alias remediation audit focused on assumed-zero rows and top-miss rows, then rerun the baseline before considering any v2 candidate draft board.
