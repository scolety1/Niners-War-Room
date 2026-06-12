# Build Sprint 5Z: Expanded Internal Validation Package

## Scope

Sprint 5Z runs an expanded internal-only validation package on the 2020-2024 legal trainable universe. It is aggregate-only and internal-only.

This sprint did not create app percentage values, public/player-facing probabilities, rankings, app-readable probability tables, per-player prediction exports, promoted model artifacts, push, deploy, or active app/ranking logic changes.

## Local Outputs

Local-only outputs were written under:

`local_exports/outcome_probability/sprint_5z_expanded_internal_validation_package/`

Created files:

- `expanded_internal_validation_metadata.json`
- `expanded_internal_validation_metrics.csv`
- `expanded_internal_validation_bin_summary.csv`
- `expanded_internal_validation_coefficient_sanity.csv`
- `expanded_internal_validation_feature_sanity.csv`
- `expanded_internal_validation_output_audit.csv`
- `expanded_internal_validation_blocked_paths.csv`
- `production_readiness_blockers.csv`
- `forbidden_feature_scan.csv`
- `README_SPRINT_5Z.md`

## Metadata Contract

Run metadata:

- `run_id`: `sprint_5z_expanded_internal_validation_2020_2022_validate_2023_test_2024`
- `feature_schema_version`: `sprint_5r_renamed_lineage_schema_v1`
- `label_schema_version`: `nwr_same_year_outcome_labels_v1`
- `benchmark_policy_id`: `nwr_v0_internal_benchmark_policy_20260611`
- `component_policy_id`: `truth_set_v0_component_supplemented_internal_v1`
- `source_manifest_version`: `player_stats_completed_prior_season_available_feb15_v1_plus_sprint_5r_compat`
- `row_family`: `all_player_pre_week1`
- `renamed_feature_schema_required`: `true`
- `feature_lineage_required`: `true`
- `forbidden_feature_scan_passed`: `true`
- `player_output_block`: `true`
- `app_output_block`: `true`
- `promotion_allowed`: `false`
- `calibration_allowed`: `false`
- `production_artifact`: `false`

## Split

Default expanded split:

- Train: 2020, 2021, 2022
- Validation: 2023
- Test: 2024

Rows:

- Train rows: 1,291
- Validation rows: 412
- Test rows: 415

## Outcomes

Modeled internally for aggregate validation mechanics:

- `same_year_difference_maker`
- `same_year_starter`
- `same_year_useful`
- `same_year_replacement_or_bust`

Blocked:

- `next_year_starter`
- multi-year outcomes
- hazard windows
- calibration layers
- app/player-facing outputs

## Aggregate Metrics

Validation and test aggregate metrics:

| Outcome | Split | Rows | Events | Predicted mean | Observed rate | Brier | Log loss |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `same_year_difference_maker` | validation | 412 | 29 | 0.109840 | 0.070388 | 0.053720 | 0.198507 |
| `same_year_difference_maker` | test | 415 | 27 | 0.109579 | 0.065060 | 0.049472 | 0.179869 |
| `same_year_starter` | validation | 412 | 59 | 0.149037 | 0.143204 | 0.085016 | 0.279522 |
| `same_year_starter` | test | 415 | 58 | 0.150386 | 0.139759 | 0.081977 | 0.269428 |
| `same_year_useful` | validation | 412 | 91 | 0.213053 | 0.220874 | 0.102262 | 0.330438 |
| `same_year_useful` | test | 415 | 91 | 0.215073 | 0.219277 | 0.111498 | 0.361745 |
| `same_year_replacement_or_bust` | validation | 412 | 321 | 0.786947 | 0.779126 | 0.102262 | 0.330438 |
| `same_year_replacement_or_bust` | test | 415 | 324 | 0.784927 | 0.780723 | 0.111498 | 0.361745 |

These are internal mechanics diagnostics only. No calibration layer was used.

## Output-Block Audit

Output-block audit passed:

- No `player_id`.
- No `player_name`.
- No row ID.
- No per-player probability.
- No app-compatible probability table.
- No production model artifact.
- No ranking/sort output.

Only aggregate metrics, aggregate bins, coefficient sanity, feature sanity, blocked-path tables, and metadata were written.

## Feature Scan

Forbidden-feature scan passed with 0 blockers across all 17 package features, including encoded position features.

Blocked feature/source contexts remain excluded:

- Old ambiguous names.
- Same-season stats.
- Target labels as features.
- Public fantasy totals.
- ADP.
- Projections.
- Rankings.
- Market/trade values.
- Prior fantasy draft history.
- Legacy `private_score`.
- Label supplement sources as prediction features.

## Warnings

Sprint 5Z passes with warnings because:

- The package is internal-only and aggregate-only.
- No calibration layer is approved.
- `next_year_starter` remains blocked.
- Production/app readiness is still blocked.
- Position-specific or display calibration remains future-gated.

## Verdict

`EXPANDED_INTERNAL_VALIDATION_PASS_WITH_WARNINGS`

Sprint 5AA calibration feasibility gate can start. Production/app modeling remains blocked.

## Confirmed Non-Actions

- No app percentage values created.
- No calibrated probabilities created.
- No public/player-facing probabilities created.
- No rankings created.
- No push or deploy occurred.
- No active app/ranking logic modified.
- No promoted or released model artifact.
