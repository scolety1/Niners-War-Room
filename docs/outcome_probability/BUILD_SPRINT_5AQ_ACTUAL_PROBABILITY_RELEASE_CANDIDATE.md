# Build Sprint 5AQ: Actual Probability Release Candidate

## Verdict

`BLOCKED_BY_2026_FEATURE_COVERAGE`

No actual 2026 outcome probabilities are accurate enough to show in the app yet.
No exact percentages are safe to release. No coarse probability bands are safe to
release. Status-only player-detail display remains the only approved app-facing
outcome surface.

This audit did not wire probabilities into the app, create fake probabilities,
create placeholder probabilities, create app-readable probability tables, change
rankings/sorting, push, deploy, or promote a model artifact.

## Local Outputs

Local-only exports were written under:

`local_exports/outcome_probability/sprint_5aq_actual_probability_release_candidate/`

Created files:

- `threshold_target_support.csv`
- `threshold_validation_metrics.csv`
- `threshold_calibration_audit.csv`
- `threshold_monotonicity_audit.csv`
- `current_2026_prediction_coverage.csv`
- `current_2026_prediction_coverage_summary.csv`
- `release_candidate_decision_table.csv`
- `blocked_probability_targets.csv`
- `metadata_sprint_5aq.json`
- `README_SPRINT_5AQ.md`

## Evidence Used

Committed evidence reviewed:

- Sprint 5X 2020-2022 historical rebuild.
- Sprint 5Y expanded calibration readiness.
- Sprint 5Z expanded internal validation package.
- Sprint 5AA calibration feasibility gate.
- Sprint 5AD internal calibration audit.
- Current measurable app pool from `sample_data/2026_pre_declaration`.

The referenced local 5N/5Z/5AA per-row export folders are not present in this
clone. Sprint 5AQ therefore uses committed aggregate evidence and blocks any
release decision that would require unavailable per-player prediction rows,
calibration bins, or direct threshold-head output.

## Historical Support

Expanded historical trainable universe:

- Train 2020-2022: 1,291 rows.
- Validation 2023: 412 rows.
- Test 2024: 415 rows.
- Total 2020-2024 trainable rows: 2,118.
- Position support: QB 307, RB 538, WR 817, TE 456.

Outcome support:

| Target | Events | Non-events | Event rate | Recommendation |
| --- | ---: | ---: | ---: | --- |
| `same_year_difference_maker` | 150 | 1,968 | 0.0708 | `internal_only` |
| `same_year_starter` | 293 | 1,825 | 0.1383 | `internal_only` |
| `same_year_useful` | 454 | 1,664 | 0.2144 | `internal_only` |
| `same_year_replacement_or_bust` | 1,664 | 454 | 0.7856 | `internal_only` |
| `next_year_starter` | 194 | 1,102 observed | 0.1497 observed only | `blocked_sparse_events` |

The historical label schema supports broad same-year targets. It does not yet
provide release-ready direct position-specific threshold heads for the requested
app columns:

- QB: T6, T12, T18, T24.
- RB: T6, T12, T24, T36, T48.
- WR: T6, T12, T24, T36, T48.
- TE: T3, T6, T12, T18, T24.

Generic app columns must be interpreted by position. QB T36/T48 and TE T36/T48
are not applicable. No generic T column should be displayed as if every position
has the same valid threshold set.

## Validation Metrics

Aggregate internal validation/test metrics from Sprint 5Z:

| Target | Split | Rows | Events | Predicted mean | Observed rate | Brier | Log loss |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `same_year_difference_maker` | validation | 412 | 29 | 0.109840 | 0.070388 | 0.053720 | 0.198507 |
| `same_year_difference_maker` | test | 415 | 27 | 0.109579 | 0.065060 | 0.049472 | 0.179869 |
| `same_year_starter` | validation | 412 | 59 | 0.149037 | 0.143204 | 0.085016 | 0.279522 |
| `same_year_starter` | test | 415 | 58 | 0.150386 | 0.139759 | 0.081977 | 0.269428 |
| `same_year_useful` | validation | 412 | 91 | 0.213053 | 0.220874 | 0.102262 | 0.330438 |
| `same_year_useful` | test | 415 | 91 | 0.215073 | 0.219277 | 0.111498 | 0.361745 |
| `same_year_replacement_or_bust` | validation | 412 | 321 | 0.786947 | 0.779126 | 0.102262 | 0.330438 |
| `same_year_replacement_or_bust` | test | 415 | 324 | 0.784927 | 0.780723 | 0.111498 | 0.361745 |

`same_year_difference_maker` overpredicts the holdout event rate at the aggregate
mean level. The broader same-year targets are directionally closer, but none has
a released calibration layer or player-level monotonicity audit.

`next_year_starter` has no valid 2024 test window and remains blocked.

## Calibration Findings

Calibration is not release-ready:

- No calibration layer is released.
- Platt-style calibration remains future/internal-only.
- Isotonic calibration remains blocked by sparse/zero-event bins.
- Position-specific calibration remains blocked by unstable position slices.
- ECE/bin-error cannot be safely recomputed in this clone because the local
  5Z bin export folder is absent.

The 5AD audit found aggregate same-year outcomes suitable for internal
calibration discussion, not app/player-facing release.

## Monotonicity Findings

Exact or banded app release requires player-level monotonic checks for each
position-specific emitted chain, for example:

- QB: T6 <= T12 <= T18 <= T24.
- RB/WR: T6 <= T12 <= T24 <= T36 <= T48.
- TE: T3 <= T6 <= T12 <= T18 <= T24.

Sprint 5AQ did not create player-level probabilities. No legal player-level
prediction rows are present locally. Monotonicity is therefore
`not_evaluable_no_player_level_predictions` and blocks exact percentages and
coarse bands.

## 2026 Prediction Coverage

Measured current app/sample rankings pool:

| Metric | Value |
| --- | ---: |
| Total players in app rankings pool | 24 |
| Rows with legal 2026 prediction features | 0 |
| Rows missing required features | 24 |
| Rows not applicable | 0 |
| Rows blocked by release gate | 24 |
| Rows blocked by missing identity | 24 |
| Rows blocked by missing prior-season data | 24 |
| Rookies supported | 0 |

Position counts:

- QB: 2.
- RB: 5.
- TE: 4.
- WR: 13.

The configured `local_exports` active data pack and current-player value rows
are absent in this clone, so coverage was measured from the sample pack that the
local app can display. Every measured row remains blocked by missing current
Model v4 identity/current-player rows and by missing legal 2026 outcome feature
snapshots.

Rookies are not supported by forcing veteran prior-season features onto them.
They require a separate rookie head/model or remain blocked.

## Release Decision

No exact percentages are safe to release.

No coarse bands are safe to release.

Blocked targets:

- All requested direct 2026 position-threshold columns: QB T6/T12/T18/T24,
  RB T6/T12/T24/T36/T48, WR T6/T12/T24/T36/T48, TE T3/T6/T12/T18/T24.
- Broad same-year internal labels remain `internal_only`.
- `next_year_starter` remains blocked by censoring/validation.
- Multi-year and hazard targets remain not applicable/blocked.

Rankings-table probability display is not allowed. Player-detail probability
display is not allowed either; only status-only text remains allowed. Sorting by
outcome probabilities remains blocked.

## App Wiring Decision

App wiring should not start next.

Do next:

1. Build direct legal position-specific threshold labels/heads for the requested
   2026 app columns.
2. Recreate or restore the expanded historical local export folders needed for
   per-row/bin audits.
3. Run aggregate-only train 2020-2022, validation 2023, test 2024 validation for
   each direct target/head.
4. Run rolling-origin diagnostics.
5. Run calibration-bin and simple Platt feasibility audits internally only.
6. Build legal 2026 prediction feature snapshots and coverage audit.
7. Run player-level monotonicity checks before any display decision.

Do not do next:

1. Do not wire probabilities into app pages.
2. Do not show exact percentages.
3. Do not show coarse probability bands.
4. Do not add rankings-table probability columns.
5. Do not sort by outcome probabilities.
6. Do not promote model artifacts.
7. Do not use forbidden feature sources.

## Final Recommendation

`BLOCKED_BY_2026_FEATURE_COVERAGE`

This is stricter than `INTERNAL_ONLY_MORE_VALIDATION_NEEDED` because the current
2026 app/sample pool has zero rows with legal prediction features and all
measured rows are release-gate blocked. Historical aggregate metrics can guide
future internal work, but they do not justify app-facing probability output.
