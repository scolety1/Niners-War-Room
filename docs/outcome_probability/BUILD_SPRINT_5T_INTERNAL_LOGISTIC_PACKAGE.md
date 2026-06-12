# Build Sprint 5T: Internal Logistic Package

Status: `INTERNAL_LOGISTIC_PACKAGE_PASS_WITH_WARNINGS`

Sprint 5T created a metadata-gated, internal-only logistic mechanics package for same-year outcomes. It did not create app percentage values, public/player-facing probabilities, rankings, app-readable probability tables, production model artifacts, push, deploy, or modify active app/ranking logic.

## Scope

Approved by the Sprint 5S gate:

- Broader 827-row historical training set.
- Supplemented internal v0 benchmark.
- Renamed Sprint 5R feature schema.
- Feature lineage metadata contract.
- Train `2023` -> test `2024` diagnostic split.
- Same-year outcomes only.

This sprint packages internal mechanics only. It is not a calibrated model sprint and does not change production/app readiness.

## Code Added

Added:

- `src/services/nwr_outcome_internal_model_package_service.py`
- `tests/test_nwr_outcome_internal_model_package_service.py`

The service builds local-only aggregate diagnostics from the Sprint 5N broader historical snapshots and label linkage. It canonicalizes legacy snapshot feature keys into the renamed Sprint 5R schema before package validation. The package fails if old ambiguous names, public/ranking/market/projection/private score fields, same-season fields, target labels, or label supplement feature sources survive into the canonical feature list.

## Metadata Contract

The emitted package metadata includes:

- `run_id`: `sprint_5t_internal_logistic_2023_train_2024_test`
- `feature_schema_version`: `sprint_5r_renamed_lineage_schema_v1`
- `label_schema_version`: `nwr_same_year_outcome_labels_v1`
- `benchmark_policy_id`: `nwr_v0_internal_benchmark_policy_20260611`
- `component_policy_id`: `truth_set_v0_component_supplemented_internal_v1`
- `source_manifest_version`: `sprint_5n_broader_historical_rebuild`
- `training_seasons`: `2023`
- `test_seasons`: `2024`
- `row_family`: `all_player_pre_week1`
- `renamed_feature_schema_required`: `true`
- `feature_lineage_required`: `true`
- `forbidden_feature_scan_passed`: `true`
- `player_output_block`: `true`
- `app_output_block`: `true`
- `promotion_allowed`: `false`
- `calibration_allowed`: `false`
- `production_artifact`: `false`

Training rows:

- Train rows: `412`
- Test rows: `415`

## Feature Schema

Used renamed legal features only:

- `age_at_snapshot`
- `experience_at_snapshot`
- `position`
- `prior_completed_season_games_played`
- `prior_completed_season_passing_yards`
- `prior_completed_season_receiving_first_downs`
- `prior_completed_season_receiving_yards`
- `prior_completed_season_receptions`
- `prior_completed_season_rushing_first_downs`
- `prior_completed_season_rushing_yards`
- `prior_season_nwr_finish_rank`
- `prior_season_nwr_ppg`

Allowed-but-not-present optional names such as `prior_completed_season_games` and `prior_completed_season_games_active` were not invented.

Forbidden feature scan result: `pass`

## Outcomes

Modeled internally:

- `same_year_difference_maker`
- `same_year_starter`
- `same_year_useful`
- `same_year_replacement_or_bust`

Blocked:

- `next_year_starter`
- multi-year outcomes
- hazard windows

## Logistic Mechanics

Model family:

- `regularized_logistic_mechanics`

Controls:

- Train season: `2023`
- Test season: `2024`
- Simple regularized logistic mechanics
- Train-set standardization for numeric design stability
- No calibration layer
- No model promotion
- No saved production model object
- No player-level prediction export
- No app-compatible probability table

Aggregate diagnostics:

| Outcome | Train events | Test events | Aggregate predicted mean | Observed rate | Brier score | Log loss |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `same_year_difference_maker` | 29 | 27 | 0.072324 | 0.065060 | 0.050794 | 0.179851 |
| `same_year_starter` | 59 | 58 | 0.144382 | 0.139759 | 0.086095 | 0.282338 |
| `same_year_useful` | 91 | 91 | 0.222422 | 0.219277 | 0.112095 | 0.364155 |
| `same_year_replacement_or_bust` | 321 | 324 | 0.777578 | 0.780723 | 0.112095 | 0.364155 |

These are aggregate internal diagnostics only. They are not calibrated probabilities and must not be displayed in the app.

## Output Block Audit

Blocked and verified absent:

- Player-level predictions
- App probability table
- Production model artifact
- Rankings or sortable model scores

CSV diagnostic headers were checked for:

- `player_id`
- `player_name`
- `row_id`
- `predicted_probability`

None of the Sprint 5T diagnostic CSV headers include those fields.

## Local Outputs

Sprint 5T wrote local-only exports under:

`local_exports/outcome_probability/sprint_5t_internal_logistic_package/`

Created outputs:

- `internal_logistic_package_metadata.json`
- `internal_logistic_outcome_metrics.csv`
- `internal_logistic_bin_summary.csv`
- `internal_logistic_coefficient_sanity.csv`
- `internal_logistic_feature_sanity.csv`
- `blocked_output_audit.csv`
- `forbidden_feature_scan.csv`
- `production_readiness_blockers.csv`
- `README_SPRINT_5T.md`

## Warnings

- This package has only one forward diagnostic split: `2023 -> 2024`.
- No calibration layer is allowed.
- No calibration holdout exists.
- `next_year_starter` remains blocked/censored.
- Coefficient sanity is internal only and not a production explanation layer.

## Production Readiness

Production/app modeling remains blocked.

Remaining blockers:

- More seasons beyond 2023/2024.
- True calibration holdout.
- Mature next-year/multi-year labels or explicit exclusion.
- Confidence gate.
- App display gate.
- Final leakage audit.
- Model card/release policy.
- Explicit HQ approval.

## Verdict

Verdict: `INTERNAL_LOGISTIC_PACKAGE_PASS_WITH_WARNINGS`

Future internal work may continue under the Sprint 5S gate. App-facing calibrated probabilities remain blocked.

## Safety Confirmation

No app percentages, calibrated probabilities, player-facing probabilities, rankings, push, or deploy occurred.
