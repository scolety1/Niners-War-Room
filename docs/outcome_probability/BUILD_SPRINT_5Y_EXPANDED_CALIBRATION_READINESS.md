# Build Sprint 5Y: Expanded Calibration Readiness

## Scope

Sprint 5Y reassesses validation and calibration readiness using the expanded 2020-2024 legal trainable universe.

This sprint did not train promoted models, create app percentage values, create public/player-facing probabilities, create rankings, push, deploy, modify active app/ranking logic, promote or release model artifacts, or create app-readable probability tables.

## Local Outputs

Local-only outputs were written under:

`local_exports/outcome_probability/sprint_5y_expanded_calibration_readiness/`

Created files:

- `expanded_outcome_support_by_season_position.csv`
- `expanded_validation_scenarios.csv`
- `expanded_calibration_feasibility.csv`
- `expanded_next_year_label_maturity.csv`
- `expanded_feature_schema_audit.csv`
- `expanded_readiness_blockers.csv`
- `README_SPRINT_5Y.md`

## Inputs Inspected

Expanded trainable universe:

- Sprint 5X rebuilt 2020-2022 rows.
- Sprint 5N approved 2023/2024 rows.
- Sprint 5R feature rename/lineage compatibility layer for the 2023/2024 rows.

Total expanded trainable rows: 2,118

By season:

- 2020: 418
- 2021: 439
- 2022: 434
- 2023: 412
- 2024: 415

## Expanded Outcome Support

All same-year outcomes have both event and non-event classes across the expanded 2020-2024 universe.

Expanded all-position support:

| Outcome | Events | Non-events | Event rate |
| --- | ---: | ---: | ---: |
| `same_year_difference_maker` | 150 | 1,968 | 0.0708 |
| `same_year_starter` | 293 | 1,825 | 0.1383 |
| `same_year_useful` | 454 | 1,664 | 0.2144 |
| `same_year_replacement_or_bust` | 1,664 | 454 | 0.7856 |
| `next_year_starter` | 194 | 1,102 | 0.1497 observed only |

`next_year_starter` remains partial because missing/censored next-year rows are not converted to false labels.

Position-level same-year support is usable for internal validation, but some TE/difference-maker and other thin position/outcome slices remain sparse. Position-specific calibration remains blocked.

## Validation Readiness

Scenario classifications:

- `train_2020_2022_validate_2023_test_2024`: `valid_internal_validation`
- `train_2020_2021_validate_2022_test_2023_2024`: `valid_internal_validation`
- `rolling_origin_validation`: `valid_internal_diagnostic`
- `pooled_resampling_mechanics_only`: `mechanics_only`
- `reverse_time_diagnostics_only`: `mechanics_only`
- `production_calibration_readiness`: `blocked_for_production`

The best current internal validation path is:

`train 2020-2022 -> validate 2023 -> test 2024`

Allowed outcomes for this path are same-year outcomes only.

## Calibration Feasibility

Calibration remains internal-only and not app-ready.

Assessment:

- No calibration: `allowed_internal_feasibility_only`
- Platt calibration: `allowed_internal_feasibility_only`
- Outcome-specific calibration: `allowed_internal_feasibility_only` for same-year outcomes only
- Calibration-by-bin: `allowed_internal_feasibility_only` for aggregate bins only
- Isotonic calibration: `blocked_sparse_events`
- Position-specific calibration: `blocked_unstable_position_slices`
- Confidence-band display: `blocked_for_production`

No calibration was run in this sprint.

## Next-Year Label Maturity

| Target season | Observed next-year rows | Events | Non-events | Missing/censored | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| 2020 | 331 | 47 | 284 | 87 | `mature_partially_observed` |
| 2021 | 333 | 52 | 281 | 106 | `mature_partially_observed` |
| 2022 | 313 | 46 | 267 | 121 | `mature_partially_observed` |
| 2023 | 319 | 49 | 270 | 93 | `mature_partially_observed` |
| 2024 | 0 | 0 | 0 | 415 | `censored_future_window` |

`next_year_starter` is not ready for production calibration. Missing or censored future windows remain null/missing and are not treated as false outcomes.

## Feature And Schema Audit

Feature/schema audit passed:

- 5X full exports use renamed Sprint 5R schema.
- 5N 2023/2024 rows are covered by Sprint 5R rename/lineage compatibility.
- Old ambiguous feature-name hits: 0.
- Forbidden feature hits: 0.
- Source-season-before-target issues: 0.
- Derived-availability-before-cutoff issues: 0.
- Lineage metadata present.

The expanded readiness assessment is safe for internal validation planning only.

## Remaining Blockers

Production/app modeling remains blocked by:

- Final leakage audit.
- Calibration validation and stability evidence.
- Confidence/display gates.
- App-output/player-output gate.
- Release policy.
- Explicit HQ approval.
- `next_year_starter` censoring/partial observation.
- Sparse position-specific calibration slices.

## Verdict

`READY_FOR_5Z_EXPANDED_INTERNAL_VALIDATION`

Sprint 5Z expanded internal validation can start. Production/app modeling remains blocked.

## Confirmed Non-Actions

- No promoted models trained.
- No calibrated probabilities created.
- No app percentage values created.
- No public/player-facing probabilities created.
- No rankings created.
- No push or deploy occurred.
- No active app/ranking logic modified.
- No model artifact promoted or released.
