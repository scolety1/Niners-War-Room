# Build Sprint 4C: Collapsed V0 Benchmark

Status: implemented as an internal-only benchmark export.

Sprint 4C takes the limited Sprint 4 v0 base-rate rows and creates a safer collapsed benchmark layer. It does not train calibrated models, does not create player-facing probabilities, does not create app percentage values, and does not create rankings.

## Input

- Source export: `local_exports/outcome_probability/sprint_4_v0_base_rates/base_rate_bucket_results.csv`
- Scope retained on outputs: `limited_truth_set_v0`
- Component waiver retained on outputs: `truth_set_v0_component_waiver_v1`
- Internal-only flag retained on benchmark outputs: `true`

## Kept Bucket Families

These bucket families are retained as direct internal benchmark rows:

- `position`
- `position_cohort`

They are the only Sprint 4 bucket families with enough stability to be used as the first internal benchmark layer.

## Collapsed Bucket Families

These families are kept only as lineage/audit context and collapsed to parent-level benchmark interpretation:

- `prior_finish_tier`
- `trailing_ppg_tier`
- `games_played_tier`

The child buckets are too sparse for direct use. They remain useful for future analysis, but Sprint 4C does not publish them as direct benchmark buckets.

## Disabled Bucket Families

- `age_band`

Age-band buckets are disabled because the current source path still lacks reliable registered age/date-of-birth coverage. Age should not be used as a benchmark dimension until identity and date coverage are registered and audited.

## Kept Outcomes

Sprint 4C keeps only same-year outcomes:

- `same_year_difference_maker`
- `same_year_starter`
- `same_year_useful`
- `same_year_replacement_or_bust`

## Disabled Outcomes

- `next_year_starter`

`next_year_starter` remains disabled for this collapsed benchmark because the support/censoring profile is not strong enough for a safer internal benchmark.

## Export Files

Sprint 4C writes local-only outputs under:

`local_exports/outcome_probability/sprint_4c_collapsed_v0_benchmark/`

Expected files:

- `collapsed_v0_benchmark.csv`
- `disabled_bucket_families.csv`
- `disabled_outcomes.csv`
- `collapsed_bucket_lineage.csv`
- `benchmark_readiness_summary.csv`
- `README_SPRINT_4C.md`

## Readiness Labels

Collapsed benchmark rows are labeled for internal readiness:

- `usable_internal_parent_prior`
- `sparse_internal_prior`
- `disabled_missing_age`
- `disabled_censored_or_unstable`

These labels are intended for benchmark governance, not app display.

## Guardrails

- These exports are not calibrated probabilities.
- These exports are not app-ready percentages.
- These exports are not public/player-facing probabilities.
- These exports are not rankings.
- Banned market, public ranking, projection, ADP, trade-calculator, prior draft, and legacy private-score fields remain excluded from predictive use.
- Component waiver disclosure is required on every benchmark row.

## Sprint 5 Status

Sprint 5 calibrated model work remains blocked. The next safe step is to audit Sprint 4C outputs and decide whether the collapsed internal benchmark is sufficient for non-app benchmark comparison, or whether source coverage and component waivers must be improved first.
