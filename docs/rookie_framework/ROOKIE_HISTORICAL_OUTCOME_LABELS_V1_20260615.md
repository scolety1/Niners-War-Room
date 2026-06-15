# Rookie Historical Outcome Labels v1 - 2026-06-15

## Executive Verdict

Verdict: GREEN for building a local-only historical outcome label package, YELLOW for immediate tuning readiness.

The rookie lane now has evaluation-only labels for the 2021-2025 historical rookie feature rows. These labels are intended for later backtest and tuning work only. They are not rookie-time features, production rankings, private scores, app outputs, probabilities, bands, hidden sort keys, or promoted artifacts.

No tuning was performed in this step.

## Files Inspected

- `local_exports/model_v4/current_value/latest/full_board_active_support/evidence_matrices/historical_rookie_backtest_feature_matrix.csv`
- `local_exports/truth_set_lab/v3/downloads/player_stats.csv`
- `local_exports/truth_set_lab/v3/downloads/player_stats_2025.csv`
- `scripts/rookie_framework/build_rookie_draft_ranking_v01.py`
- `scripts/rookie_framework/backtest_rookie_ranking_model_v01.py`
- `scripts/rookie_framework/tune_rookie_ranking_model_v01.py`

## Files Created

- `scripts/rookie_framework/build_rookie_historical_outcome_labels_v1.py`
- `tests/test_rookie_historical_outcome_labels_v1.py`
- `docs/rookie_framework/ROOKIE_HISTORICAL_OUTCOME_LABELS_V1_20260615.md`

## Local-Only Exports Created

Local-only export directory:

`local_exports/rookie_framework/historical_outcome_labels_v1_20260615/`

Exports:

- `rookie_historical_outcome_labels_v1_20260615.csv`
- `rookie_historical_label_coverage_summary_20260615.csv`
- `rookie_historical_label_quality_issues_20260615.csv`
- `rookie_historical_backtest_readiness_20260615.csv`
- `README_ROOKIE_HISTORICAL_OUTCOME_LABELS_V1_20260615.md`

These exports are not committed and must remain local-only unless a separate approval path explicitly promotes a tracked summary.

## Labels Built

Total label rows: 395

Quality counts:

- `GREEN_COMPLETE_LABEL`: 215
- `YELLOW_ASSUMED_ZERO_NO_RECORDED_STATS`: 20
- `YELLOW_PARTIAL_WINDOW`: 160
- `RED_NO_LABEL`: 0

Readiness counts:

- Backtest-ready complete-window rows: 235
- Partial-window rows: 160
- Market/ROI labels: 0, blocked because no admitted display-only rookie-cost source is registered for this package

## Class-Year Coverage

| Rookie class | Rows | Matched stat rows | Assumed-zero rows | Partial rows | Feasibility |
|---|---:|---:|---:|---:|---|
| 2021 | 76 | 67 | 9 | 0 | GREEN_LABELABLE |
| 2022 | 79 | 75 | 4 | 0 | GREEN_LABELABLE |
| 2023 | 80 | 73 | 7 | 0 | GREEN_LABELABLE |
| 2024 | 76 | 67 | 0 | 76 | YELLOW_PARTIAL_LABELS |
| 2025 | 84 | 66 | 0 | 84 | YELLOW_PARTIAL_LABELS |

2021-2023 can support a first-three-year historical replay using complete windows. The 2024 and 2025 classes are partial because future seasons do not exist yet.

## Label Definitions

The package creates these outcome labels:

- `label_year1_points`, `label_year2_points`, `label_year3_points`
- `label_year1_pos_rank`, `label_year2_pos_rank`, `label_year3_pos_rank`
- `label_year1_starter_flag`, `label_year2_starter_flag`, `label_year3_starter_flag`
- `label_first3_total_points`
- `label_first3_best_season_points`
- `label_first3_best_pos_rank`
- `label_first3_starter_seasons`
- `label_first3_zero_or_low_value_flag`
- `label_bust_flag`
- `label_star_flag`
- `label_useful_flag`

The package also creates evaluation-only metadata:

- `eval_label_source`
- `eval_join_method`
- `eval_backtest_ready_flag`

Market comparison columns are present only as blocked display/evaluation placeholders:

- `market_display_rookie_pick_cost`
- `eval_roi_vs_market_cost`
- `eval_reach_flag`
- `eval_value_pick_flag`

## Scoring Fit

The label builder reconstructs Tim's non-PPR scoring from source-safe raw NFL stat components:

- Passing yards: 1 per 30
- Passing TD: 3
- Interception: -1
- Rush/receiving yards: 1 per 10
- Rush/receiving TD: 4
- Rush/receiving first downs: 0.4
- Return yards: 1 per 30 when source columns exist
- Special teams TD: 4
- Two-point conversions: 2
- Fumbles lost: -1

First-down scoring is included from rushing and receiving first-down source columns. Return-yard scoring is complete for 2025 where punt and kickoff return yard columns are present. Return-yard scoring is partial for 2021-2024 because those local weekly source files do not expose return-yard columns; the package marks that quality caveat instead of inventing values.

## Leakage Controls

Labels are post-rookie evaluation targets only. They are generated from NFL outcome stats after the rookie class season and are not merged back into rookie-time features.

The package does not:

- create production rankings
- overwrite private scores
- create probabilities or bands
- create hidden sort keys
- wire app or Streamlit outputs
- touch Outcome HQ files, outcome columns, veteran files, or veteran outcome heads
- use ADP, public rankings, projections, consensus, trade calculators, or market values as private score inputs

## Quality Issues

The quality issue export contains 217 caveat rows.

The two expected caveat classes are:

- Assumed-zero no-recorded-stat seasons for players with no matching weekly stat row in an already completed season.
- Future-unavailable seasons for 2024 and 2025 class rows.

These are not silently included as clean labels. They remain visible through `label_quality_status`, `label_missing_reason`, and `eval_backtest_ready_flag`.

## Backtest Readiness

Backtest readiness: partially ready.

The 235 complete-window rows from 2021-2023 are ready for a later replay/backtest join. The current backtest/tuning scaffolds still need a separate rookie-only patch to consume this label package explicitly and to exclude or separately handle partial-window 2024-2025 rows.

## Tuning Readiness

Tuning readiness: blocked pending a separate backtest integration step.

No tuning should run until:

- the backtest scaffold joins this label package intentionally
- complete-window versus partial-window handling is explicit
- star/useful/bust targets are validated against the replay objective
- market/ROI labels remain blocked or get an approved display-only cost source
- no labels are used as rookie-time features

## Commands Run

- `git rev-parse --show-toplevel`
- `git branch --show-current`
- `git status --short`
- `git log --oneline -8`
- `python scripts/rookie_framework/build_rookie_historical_outcome_labels_v1.py`
- `python -m py_compile scripts/rookie_framework/build_rookie_historical_outcome_labels_v1.py`
- `python tests/test_rookie_historical_outcome_labels_v1.py`
- `python -m pytest tests/test_rookie_historical_outcome_labels_v1.py -q`
- `python scripts/rookie_framework/build_rookie_review_board_v03.py --strict`
- `python scripts/rookie_framework/build_rookie_shadow_ranking_v03.py --strict`
- `python scripts/rookie_framework/build_rookie_production_candidate_v03.py --strict`
- `python scripts/rookie_framework/build_rookie_analyzer_v03.py --strict`
- `python scripts/rookie_framework/build_rookie_draft_day_simulation_v03.py --strict`
- `python scripts/rookie_framework/build_rookie_draft_ranking_v01.py`
- `python scripts/rookie_framework/backtest_rookie_ranking_model_v01.py`
- `python scripts/rookie_framework/tune_rookie_ranking_model_v01.py`
- direct rookie framework harnesses where available
- `git diff --check`

## Release Blockers

This package is not a production release. Blockers before production or app usage:

- no production implementation approval
- no app display contract
- no complete 2024 or 2025 first-three-year outcome windows
- no approved display-only market cost source for ROI/reach/value labels
- no joined backtest run has been reviewed yet
- tuning remains blocked until a separate approved backtest integration pass

## Exact Next Safe Step

Run a rookie-only backtest label integration audit/patch that joins `rookie_historical_outcome_labels_v1_20260615.csv` into the existing backtest scaffold, uses only 2021-2023 complete-window rows for the first replay, keeps 2024-2025 as partial evaluation rows, and still performs no production promotion.
