# Build Sprint 5B: Aggregate Baseline Mechanics

Status: aggregate-only internal mechanics experiment completed.

Sprint 5B tests whether the approved internal v0 benchmark infrastructure can produce aggregate validation diagnostics without creating player-facing probabilities, app percentage values, rankings, calibrated model artifacts, or per-player prediction exports.

## Governance Context

Benchmark policy ID:

`nwr_v0_internal_benchmark_policy_20260611`

Component policy ID:

`truth_set_v0_component_supplemented_internal_v1`

Scope:

`limited_truth_set_v0`

Internal only:

`true`

Sprint 5B remains inside the Sprint 4K governance freeze. The internal benchmark is blocked from app outcome columns, player card percentages, rank sorting, trade/decision automation, calibrated model release, production deployment, and training-row feature inputs from label supplement sources.

## Aggregate Inputs

Inputs inspected:

- Sprint 4J supplemented internal v0 benchmark
- Sprint 5A outcome support and feasibility findings
- canonical truth-set rows with approved label-layer supplements

Sprint 5B generated aggregate-only diagnostics with:

- no player IDs
- no player names
- no per-player probabilities
- no model objects
- no rankings
- no app output columns

## Exports

Local-only outputs were written under:

`local_exports/outcome_probability/sprint_5b_aggregate_baseline_mechanics/`

Files:

- `aggregate_outcome_support.csv`
- `aggregate_observed_vs_expected.csv`
- `leave_one_season_out_feasibility.csv`
- `one_class_outcome_blockers.csv`
- `benchmark_mechanics_verdict.csv`
- `README_SPRINT_5B.md`

## Outcome Support Summary

| Outcome | Event Count | Non-Event Count | Censored/Null Count | Mechanics Status |
| --- | ---: | ---: | ---: | --- |
| `same_year_difference_maker` | 148 | 18 | 0 | aggregate mechanics supported |
| `same_year_starter` | 166 | 0 | 0 | blocked by one-class/saturated outcome |
| `same_year_useful` | 166 | 0 | 0 | blocked by one-class/saturated outcome |
| `same_year_replacement_or_bust` | 0 | 166 | 0 | blocked by one-class/saturated outcome |
| `next_year_starter` | 96 | 0 | 70 | blocked by censoring |

Only `same_year_difference_maker` has both event and non-event support in the current limited truth-set universe. The other outcomes can be summarized but cannot support calibration diagnostics.

## Observed-Vs-Expected Diagnostics

Sprint 5B created aggregate observed-vs-expected diagnostics by:

- outcome
- season
- position
- row family
- cohort

Results:

- aggregate observed-vs-expected rows: 120
- valid observed-vs-expected rows: 6
- benchmark posterior means used only as internal aggregate reference values

Most observed-vs-expected rows are invalid for calibration diagnostics because the held aggregate is one-class, censored, or missing a benchmark input for disabled outcomes.

## Leave-One-Season-Out Feasibility

Available seasons:

- 2022
- 2023
- 2024

Leave-one-season-out rows emitted: 15.

The leave-one-season-out setup is mechanically possible for aggregate reporting, but calibration diagnostics are invalid or weak because most outcomes are one-class/saturated and `next_year_starter` is censored/disabled.

No logistic regression, Platt calibration, isotonic calibration, hazard model, gradient boosting model, or calibrated model object was fit.

## One-Class And Sparse Blockers

Blocked outcomes:

- `same_year_starter`: one-class, all observed rows are events
- `same_year_useful`: one-class, all observed rows are events
- `same_year_replacement_or_bust`: one-class, all observed rows are non-events
- `next_year_starter`: censored and disabled from the internal benchmark

These blockers are a data-support problem, not a mechanics bug.

## Verdict

`AGGREGATE_MECHANICS_PASS_WITH_WARNINGS`

Aggregate mechanics work, but the current limited truth-set support is too saturated and narrow for true calibrated modeling.

## Next Safe Experiment

A further internal-only experiment is allowed only if it remains aggregate/local and avoids per-player probability exports. The useful next step is broader legal row coverage and materialized point-in-time feature snapshots, not model fitting.

## Production/App Status

Production/app modeling remains blocked.

Exact blockers before true calibrated modeling:

- one-class or saturated outcome distributions
- censored `next_year_starter`
- limited truth-set universe
- absent legal point-in-time feature snapshots
- weak out-of-time validation support
- missing app display gate
- final leakage audit required

No app percentages, calibrated probabilities, player-facing probabilities, rankings, push, or deploy occurred.
