# Build Sprint 5A: Calibration Feasibility

Status: internal-only feasibility study completed.

Sprint 5A evaluates whether NWR has enough legal rows, labels, outcomes, features, source manifests, and validation support to begin calibrated outcome modeling later. It does not train a production model, does not emit app percentage values, does not create player-facing probabilities, does not create rankings, and does not modify active app or ranking logic.

## Governance Context

Sprint 4K approved the supplemented v0 benchmark as the official internal reference only.

Benchmark policy ID:

`nwr_v0_internal_benchmark_policy_20260611`

Component policy ID:

`truth_set_v0_component_supplemented_internal_v1`

Scope:

`limited_truth_set_v0`

Internal only:

`true`

The following remain explicitly blocked:

- app outcome columns
- player card percentages
- public/player-facing probability display
- rank sorting
- trade/decision automation
- calibrated model release
- production deployment
- training-row feature inputs from label supplement sources

## Inputs Inspected

Sprint 5A inspected:

- Sprint 2 point-in-time row contracts
- Sprint 3C candidate prediction/feature snapshot exports
- Sprint 3C source manifest, leakage, and missingness reports
- Sprint 4J supplemented collapsed internal benchmark
- Sprint 4K internal benchmark governance policy
- canonical truth-set labels and approved label-layer supplements

Key local inputs:

- `local_exports/outcome_probability/sprint_3c_data_readiness/candidate_feature_snapshots.csv`
- `local_exports/outcome_probability/sprint_3c_data_readiness/row_family_manifest.csv`
- `local_exports/outcome_probability/sprint_3c_data_readiness/leakage_audit_report.csv`
- `local_exports/outcome_probability/sprint_4j_supplemented_v0_rebuild/supplemented_collapsed_v0_benchmark.csv`
- `local_exports/outcome_probability/sprint_4k_internal_benchmark_governance/internal_benchmark_policy.csv`

## Legal Row And Label Support

Observed support:

- canonical truth-set weekly rows: 1,183
- internal player-season label rows: 166
- supplemented collapsed benchmark rows: 64
- seasons available: 2022, 2023, 2024
- materialized legal feature snapshots: 0

The supplemented benchmark is usable as an internal reference, but the current dataset is not enough for production/app calibrated modeling.

## Outcome Support

| Outcome | Candidate Rows | Observed Rows | Events | Non-Events | Censored/Null | Feasibility |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `same_year_difference_maker` | 166 | 166 | 148 | 18 | 0 | feasible after feature snapshots |
| `same_year_starter` | 166 | 166 | 166 | 0 | 0 | feasible after feature snapshots, but lacks negative cases |
| `same_year_useful` | 166 | 166 | 166 | 0 | 0 | feasible after feature snapshots, but lacks negative cases |
| `same_year_replacement_or_bust` | 166 | 166 | 0 | 166 | 0 | blocked by sparse events |
| `next_year_starter` | 166 | 96 | 96 | 0 | 70 | blocked by censoring |

The event distribution shows the current truth-set universe is enriched. Several outcomes have no useful positive/negative separation, so they are not production-calibration ready.

## Position And Cohort Support

The current benchmark can support only very small internal reference comparisons by:

- position
- position/cohort

It cannot support richer calibrated modeling because:

- legal feature snapshots are not materialized
- next-year outcomes remain censored or disabled
- age buckets are not part of the approved Sprint 5A modeling surface
- the truth-set universe is limited and enriched

## Split Feasibility

Available seasons:

- train candidate: 2022
- validation candidate: 2023
- test candidate: 2024

This is not enough for production calibration. A tiny walk-forward toy split is possible only as local/internal feasibility work, but the calibration holdout is weak and the feature matrix is absent.

Split feasibility:

- internal benchmark reference: feasible
- production calibration split: blocked by lack of out-of-time split support
- next-year/future-window split: blocked by censoring

## Calibration Method Feasibility

| Model Family | Feasibility | Notes |
| --- | --- | --- |
| position-only baseline | feasible internal experiment | Benchmark comparison only, no player probabilities. |
| position/cohort baseline | feasible internal experiment | Benchmark comparison only, no player probabilities. |
| ridge logistic head | blocked by missing features | Needs point-in-time feature snapshots and validation splits. |
| Platt calibration | blocked by lack of out-of-time splits | No trained score source or strong holdout support. |
| isotonic calibration | blocked by sparse events | Current support is too thin for nonparametric calibration. |
| discrete-time hazard model | blocked by censoring | Future-window support is incomplete. |
| gradient boosting challenger | blocked by missing features | Legal feature matrix and broader rows are missing. |

No calibrated models were trained.

## Confidence-Gate Feasibility

Confidence gates are not ready for app or model release.

Current status:

- sample support: limited truth-set only
- missingness support: blocked because legal feature vectors are absent
- source support: label sources approved internal-only; feature sources incomplete
- OOD/support coverage: not established
- calibration evidence: not available
- benchmark agreement: internal reference available only

## Local Exports

Sprint 5A writes local-only exports under:

`local_exports/outcome_probability/sprint_5a_calibration_feasibility/`

Export files:

- `modeling_feasibility_matrix.csv`
- `outcome_event_support.csv`
- `position_event_support.csv`
- `split_feasibility_report.csv`
- `calibration_method_feasibility.csv`
- `confidence_gate_feasibility.csv`
- `sprint_5_blockers.csv`
- `README_SPRINT_5A.md`

These exports contain feasibility counts and status labels only. They are not probabilities and not model outputs.

## Readiness Verdict

`READY_FOR_INTERNAL_MODEL_EXPERIMENT_ONLY`

A later local/internal toy experiment may compare simple baseline references. It must not create app percentages, player-facing probabilities, public outputs, rankings, or promoted model artifacts.

## Production/App Modeling Status

Production/app modeling remains blocked.

Exact blockers before true Sprint 5 modeling:

- legal point-in-time feature snapshots are absent
- limited truth-set rows are not broad enough for production calibration
- out-of-time split support is weak
- next-year outcomes are censored or disabled
- app display gate is missing
- final leakage audit is required

No app percentages, calibrated probabilities, player-facing probabilities, rankings, push, or deploy occurred.
