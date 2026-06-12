# Build Sprint 5P: Internal Baseline Experiment

Status: `INTERNAL_MECHANICS_PASS_WITH_WARNINGS`

Sprint 5P ran an internal-only baseline/model-mechanics experiment against the broader historical training set created in Sprint 5N and assessed in Sprint 5O. This pass did not train or promote a production model, did not create app percentage values, did not export player-facing probabilities, did not create rankings, and did not modify active app or ranking logic.

## Scope

Approved internal benchmark policy:

- `benchmark_policy_id`: `nwr_v0_internal_benchmark_policy_20260611`
- `component_policy_id`: `truth_set_v0_component_supplemented_internal_v1`
- `scope`: `limited_truth_set_v0`
- `internal_only`: `true`

Training/test setup:

- Row family: `all_player_pre_week1`
- Train season: `2023`
- Test season: `2024`
- Train rows: `412`
- Test rows: `415`
- Total rows used by the internal mechanics run: `827`

Allowed same-year outcomes:

- `same_year_difference_maker`
- `same_year_starter`
- `same_year_useful`
- `same_year_replacement_or_bust`

Blocked outcome:

- `next_year_starter`, blocked because 2024 next-year labels remain censored/unavailable.

## Inputs

The experiment used the broader historical feature snapshots and label linkage exports from Sprint 5N:

- `local_exports/outcome_probability/sprint_5n_broader_historical_rebuild/broader_historical_feature_snapshots.csv`
- `local_exports/outcome_probability/sprint_5n_broader_historical_rebuild/broader_historical_label_linkage.csv`

Allowed feature families were limited to legal historical features:

- Age
- Position
- Experience
- Prior NWR finish rank
- Prior NWR PPG
- Prior games
- Prior first downs
- Prior receptions
- Prior rushing, receiving, and passing yards

Forbidden feature and output paths remained blocked:

- Same-season features
- Target labels as features
- Public fantasy totals as labels
- ADP, rankings, projections, market values, trade values, RotoWire rankings/projections/outlooks/values, legacy `private_score`, and prior league draft history
- Supplement label sources as prediction features
- Per-player probability exports
- App probability columns
- Rankings or player-sortable model output
- Calibrated model artifacts

## Local Outputs

Sprint 5P wrote local-only exports under:

`local_exports/outcome_probability/sprint_5p_internal_baseline_experiment/`

Created exports:

- `aggregate_baseline_results.csv`
- `logistic_mechanics_aggregate_metrics.csv`
- `logistic_mechanics_bin_summary.csv`
- `feature_coefficient_sanity.csv`
- `blocked_model_paths.csv`
- `production_readiness_blockers.csv`
- `README_SPRINT_5P.md`

The exported CSV schemas were checked for `player_id`, `player_name`, and `row_id`; none of the Sprint 5P diagnostic exports include those identifiers.

## Baseline Diagnostics

Sprint 5P created aggregate-only empirical baselines for:

- Position-only baseline
- Position/cohort baseline

At the all-position aggregate level, both baseline families matched because cohort did not add a distinct aggregate split in this diagnostic view.

| Outcome | Train events | Test events | Aggregate predicted mean | Aggregate observed rate | Expected events | Observed events | Event delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `same_year_difference_maker` | 29 | 27 | 0.070388 | 0.065060 | 29.2112 | 27 | -2.2112 |
| `same_year_starter` | 59 | 58 | 0.143204 | 0.139759 | 59.4296 | 58 | -1.4296 |
| `same_year_useful` | 91 | 91 | 0.220874 | 0.219277 | 91.6626 | 91 | -0.6626 |
| `same_year_replacement_or_bust` | 321 | 324 | 0.779126 | 0.780723 | 323.3374 | 324 | 0.6626 |

The aggregate empirical baselines were directionally coherent on the 2024 holdout. These remain descriptive benchmark diagnostics only.

## Logistic Mechanics

Sprint 5P ran an internal-only regularized logistic mechanics pass for the allowed same-year outcomes:

- No calibration layer
- No Platt scaling
- No isotonic calibration
- No hazard model
- No gradient boosting
- No model artifact saved
- No player-level probabilities exported

Aggregate logistic diagnostics:

| Outcome | Train events | Test events | Aggregate predicted mean | Aggregate observed rate | Expected events | Observed events | Event delta | Test Brier | Test log loss |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `same_year_difference_maker` | 29 | 27 | 0.071320 | 0.065060 | 29.5978 | 27 | -2.5978 | 0.048238 | 0.161267 |
| `same_year_starter` | 59 | 58 | 0.147225 | 0.139759 | 61.0982 | 58 | -3.0982 | 0.084008 | 0.266536 |
| `same_year_useful` | 91 | 91 | 0.226656 | 0.219277 | 94.0623 | 91 | -3.0623 | 0.112867 | 0.373628 |
| `same_year_replacement_or_bust` | 321 | 324 | 0.773344 | 0.780723 | 320.9377 | 324 | 3.0623 | 0.112867 | 0.373628 |

The mechanics run produced 10 aggregate bins per modeled outcome, with 415 total test rows represented per outcome and no player identifiers in the bin export.

## Coefficient Sanity

The coefficient sanity export is diagnostic only. It is not a promoted model explanation layer and must not be used for ranking, app display, or player-facing probability claims.

Notable review flags:

- `prior_nwr_ppg` was a high-magnitude coefficient for all modeled outcomes and remains leakage-sensitive.
- `prior_nwr_finish_rank` was a high-magnitude coefficient for `same_year_useful` and `same_year_replacement_or_bust` and remains leakage-sensitive.
- Position indicators were materially influential in the mechanics run.

These findings are useful for feature review, but they do not approve production model training.

## Blocked Paths

Still blocked:

- `next_year_starter`, because mature 2024 next-year labels are unavailable.
- Platt calibration and isotonic calibration, because calibration layers are forbidden in this sprint and the available split support is too thin.
- Hazard modeling, because future windows remain censored and the path is explicitly outside Sprint 5P scope.
- Gradient boosting, because it is explicitly forbidden for Sprint 5P and carries overfit risk.
- App/player-facing probabilities, because there is no display gate or approved calibrated model.
- Rankings, because ranking output is outside the Outcome Probability HQ scope.

## Verdict

Verdict: `INTERNAL_MECHANICS_PASS_WITH_WARNINGS`

The broader historical training set can support a narrow internal mechanics experiment for same-year aggregate diagnostics. The experiment shows that the pipeline can run a train-2023/test-2024 aggregate mechanics pass without leaking player-level outputs or app probabilities.

This does not change production readiness. Production/app modeling remains blocked.

## Remaining Blockers

Before any app-facing calibrated probability work, NWR still needs:

- More seasons for out-of-time validation and calibration holdout support.
- Mature next-year labels or a formal decision to exclude next-year outcomes.
- Final leakage review for prior NWR finish rank and prior NWR PPG as features.
- A calibration method approval sprint with explicit no-app-output gates.
- A confidence gate and display gate.
- Final source/legal audit before any player-facing output.
- Explicit approval before any model artifact is saved or promoted.

## Safety Confirmation

Sprint 5P created only local internal diagnostics and this documentation. It did not create app percentages, calibrated probabilities, player-facing probabilities, rankings, push, deploy, or production model artifacts.
