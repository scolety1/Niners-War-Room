# Build Sprint 5O: Internal Model Feasibility

Date: 2026-06-11

Verdict: `READY_FOR_5P_INTERNAL_BASELINE_EXPERIMENT`

Sprint 5O audits whether the broader 827-row historical training set from Sprint 5N can support a later internal-only baseline/model-mechanics experiment. It does not train or promote a calibrated model, create app percentage values, create public/player-facing probabilities, create rankings, push, deploy, or modify active app/ranking logic.

## Training Set Inspected

Source:

`local_exports/outcome_probability/sprint_5n_broader_historical_rebuild/`

Inputs:

- `broader_historical_feature_snapshots.csv`
- `broader_historical_label_linkage.csv`
- `broader_historical_snapshot_legality_audit.csv`

Training-set summary:

- rows inspected: 827
- seasons: 2023, 2024
- row family: `all_player_pre_week1`
- legality issues: 0
- feature missingness: 0 across emitted rows
- app/player-facing probability outputs: none

## Outcome Support

Aggregate support across both seasons:

| Outcome | Observed rows | Events | Non-events | Event rate | One-class | Sparse-event |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| `same_year_difference_maker` | 827 | 56 | 771 | 0.067715 | no | no |
| `same_year_starter` | 827 | 117 | 710 | 0.141475 | no | no |
| `same_year_useful` | 827 | 182 | 645 | 0.220073 | no | no |
| `same_year_replacement_or_bust` | 827 | 645 | 182 | 0.779927 | no | no |
| `next_year_starter` | 319 | 49 | 270 | 0.153605 | no | no |

`next_year_starter` has 508 censored/missing rows because 2024 next-year outcomes are unavailable.

Same-year outcomes have both classes by season and by position. `next_year_starter` is only usable as 2023 aggregate context, not a forward 2023-to-2024 diagnostic.

## Feature Support

Feature list:

- `age_at_snapshot`
- `experience_at_snapshot`
- `position`
- `prior_games_played`
- `prior_nwr_finish_rank`
- `prior_nwr_ppg`
- `prior_passing_yards`
- `prior_receiving_first_downs`
- `prior_receiving_yards`
- `prior_receptions`
- `prior_rushing_first_downs`
- `prior_rushing_yards`

Feature diagnostics:

- missingness: 0 for all emitted features
- near-constant features: none
- leakage-sensitive features: `prior_nwr_finish_rank`, `prior_nwr_ppg`
- those leakage-sensitive features are allowed only because they are derived from completed prior-season facts under the approved historical availability policy
- position coverage: QB/RB/WR/TE covered

Correlation warnings were generated for 4 near-duplicate numeric pairs at `|r| >= 0.95`; these should be reviewed before any regularized model mechanics sprint.

## Split Feasibility

| Split | Status | Allowed use |
| --- | --- | --- |
| train 2023 -> test 2024 | `valid_internal_diagnostic` | Aggregate/model-mechanics only; no production calibration. |
| train 2024 -> test 2023 | `diagnostic_only_reverse_time` | Reverse-time sanity check only. |
| pooled resampling | `mechanics_only` | Pipeline/debug mechanics only, not out-of-time validation. |
| production calibration | `invalid` | Blocked. |

Calibration remains unsafe because there are only two seasons and no robust calibration holdout.

## Model-Family Feasibility

| Model family | Feasibility |
| --- | --- |
| position-only empirical baseline | `aggregate_baseline_only` |
| position/cohort empirical baseline | `aggregate_baseline_only` |
| regularized logistic mechanics | `allowed_internal_mechanics` for same-year outcomes only |
| Platt calibration | `blocked_not_enough_seasons` |
| isotonic calibration | `blocked_not_enough_seasons` |
| discrete-time hazard | `blocked_censoring` |
| gradient boosting challenger | `blocked_not_enough_seasons` |

`next_year_starter` remains blocked/censored for any forward 2024 evaluation.

## Aggregate Observed-Vs-Expected

Train 2023 / test 2024 position-baseline aggregate diagnostics:

| Outcome | Train event rate | Expected 2024 events | Observed 2024 events | Delta |
| --- | ---: | ---: | ---: | ---: |
| `same_year_difference_maker` | 0.070388 | 29.2112 | 27 | -2.2112 |
| `same_year_starter` | 0.143204 | 59.4296 | 58 | -1.4296 |
| `same_year_useful` | 0.220874 | 91.6626 | 91 | -0.6626 |
| `same_year_replacement_or_bust` | 0.779126 | 323.3374 | 324 | 0.6626 |
| `next_year_starter` | n/a | n/a | n/a | blocked; 2024 next-year labels censored |

These are aggregate mechanics diagnostics only. No per-player prediction rows or player probabilities were exported.

## Local Exports

Sprint 5O wrote local-only outputs under:

`local_exports/outcome_probability/sprint_5o_internal_model_feasibility/`

Files:

- `outcome_support_by_season_position.csv`
- `feature_support_diagnostics.csv`
- `split_feasibility.csv`
- `model_family_feasibility.csv`
- `aggregate_observed_vs_expected.csv`
- `blocked_modeling_paths.csv`
- `sprint_5p_recommendation.csv`
- `README_SPRINT_5O.md`

## Sprint 5P Recommendation

Sprint 5P can start an internal-only baseline experiment if it stays inside these limits:

- aggregate/model-mechanics outputs only
- no app fields
- no player-facing probabilities
- no rankings
- no promoted model artifact
- no calibrated release

Allowed outcomes:

- `same_year_difference_maker`
- `same_year_starter`
- `same_year_useful`
- `same_year_replacement_or_bust`

Blocked or limited:

- `next_year_starter`, because 2024 is censored/unavailable

## Remaining Blockers Before App-Facing Calibrated Probabilities

- more seasons for out-of-time validation
- calibration holdout support
- resolved next-year censoring
- confidence gate
- display/app gate
- final leakage audit
- explicit approval for any app/player-facing probability path

Production/app modeling remains blocked.
