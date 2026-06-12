# Build Sprint 5S: Internal Model Package Gate

Status: `READY_FOR_5T_INTERNAL_LOGISTIC_PACKAGE`

Sprint 5S defines the governance gate for the next internal-only modeling phase. It clarifies which assets are approved, which work is allowed, which paths remain blocked, and what metadata must exist before any future internal mechanics run.

This sprint did not train calibrated models, create app percentage values, create public/player-facing probabilities, create rankings, push, deploy, modify active app/ranking logic, or promote/release a model artifact.

## Current Approved Internal Assets

Approved internal-only assets:

- Broader 827-row historical `all_player_pre_week1` training set from Sprint 5N.
- Supplemented internal v0 benchmark governed by `nwr_v0_internal_benchmark_policy_20260611`.
- Component policy `truth_set_v0_component_supplemented_internal_v1`.
- Renamed Sprint 5R feature schema.
- Feature lineage metadata contract.
- Train `2023` -> test `2024` diagnostic split.
- Same-year outcome scope only.

These assets are approved only for internal diagnostics/mechanics. They are not approved for app display, player-facing probabilities, rankings, production deployment, or model promotion.

## Allowed Internal-Only Work

The next phase may perform:

- Aggregate diagnostics.
- Regularized logistic mechanics on allowed same-year outcomes.
- Train `2023` -> test `2024` diagnostics.
- Feature sanity checks.
- Coefficient sanity checks.
- Local-only internal export packages.

Required controls:

- No player-facing probability export.
- No app output.
- No ranking or sortable player score.
- No model promotion.
- No calibrated probability release.
- Renamed Sprint 5R feature schema required.
- Feature lineage metadata required.
- Forbidden feature scan required.

## Blocked Work

The following remain blocked:

- App outcome columns.
- Player card percentages.
- Player-facing probability display.
- Ranking/sorting by model output.
- Trade or decision automation.
- Production model artifact.
- Platt calibration.
- Isotonic calibration.
- Hazard model.
- Gradient boosting challenger.
- `next_year_starter` modeling.
- Multi-year outcome modeling.
- Use of unrenamed/ambiguous feature names.
- Use of supplement label sources as prediction features.

## Allowed And Blocked Outcomes

Allowed for internal mechanics:

- `same_year_difference_maker`
- `same_year_starter`
- `same_year_useful`
- `same_year_replacement_or_bust`

Blocked:

- `next_year_starter`
- multi-year outcomes
- hazard windows

Reason: same-year outcomes have both classes in the 827-row broader historical set. `next_year_starter` remains blocked because 2024 next-year labels are censored/unavailable.

## Internal Run Metadata Contract

Any future internal mechanics package must carry:

- `run_id`
- `feature_schema_version`
- `label_schema_version`
- `benchmark_policy_id`
- `component_policy_id`
- `source_manifest_version`
- `training_seasons`
- `test_seasons`
- `outcomes`
- `feature_list`
- `forbidden_feature_scan_result`
- `player_output_block`
- `app_output_block`
- `promotion_allowed`

Required values/constraints:

- `feature_schema_version`: `sprint_5r_renamed_lineage_schema_v1` or later.
- `benchmark_policy_id`: `nwr_v0_internal_benchmark_policy_20260611`.
- `component_policy_id`: `truth_set_v0_component_supplemented_internal_v1`.
- `training_seasons`: explicit season list; current diagnostic package uses `2023`.
- `test_seasons`: explicit season list; current diagnostic package uses `2024`.
- `outcomes`: same-year allowed outcomes only.
- `feature_list`: renamed feature names only.
- `forbidden_feature_scan_result`: must be `pass`.
- `player_output_block`: must be `true`.
- `app_output_block`: must be `true`.
- `promotion_allowed`: must be `false`.

## Production/App Unblock Requirements

Production or app-facing modeling cannot be reconsidered until NWR has:

- More seasons beyond 2023/2024.
- A true calibration holdout.
- Mature next-year/multi-year labels or an explicit outcome exclusion decision.
- Confidence gate.
- App display gate.
- Final leakage audit.
- Model card/release policy.
- Explicit HQ approval.

Until those are complete, Sprint 5 work remains internal-only.

## Local Outputs

Sprint 5S wrote local-only exports under:

`local_exports/outcome_probability/sprint_5s_internal_model_package_gate/`

Created outputs:

- `approved_internal_assets.csv`
- `allowed_internal_work.csv`
- `blocked_modeling_paths.csv`
- `allowed_outcomes.csv`
- `internal_run_metadata_contract.csv`
- `production_unblock_requirements.csv`
- `README_SPRINT_5S.md`

## Readiness Verdict

Verdict: `READY_FOR_5T_INTERNAL_LOGISTIC_PACKAGE`

Sprint 5T may start as an internal-only logistic package if it obeys this governance gate. It may not produce app outputs, player-facing probabilities, rankings, calibrated release artifacts, or production model artifacts.

## Safety Confirmation

No app percentages, calibrated probabilities, player-facing probabilities, rankings, push, or deploy occurred.
