# Point-in-Time Manifest Contract

Verdict: `YELLOW_POINT_IN_TIME_MANIFEST_CONTRACT_DEFINED_NO_BUILD`

## Scope

The future `Point-in-Time Snapshot Manifest Builder V1` must construct evidence that proves what each feature row knew at a selected prediction anchor. It must not treat current display artifacts as historical replay proof.

## Required Outputs

- `point_in_time_snapshot_manifest.csv`
- `prediction_anchor_contract.md`
- `source_timestamp_inventory.csv`
- `feature_replay_window_matrix.csv`
- `identity_safe_join_manifest.csv`
- `leakage_diagnostics.md`
- `non_activation_guardrail_report.md`

## Required Manifest Fields

- `dataset_id`
- `feature_family`
- `prediction_anchor`
- `source_snapshot_id`
- `source_artifact_path`
- `source_extraction_timestamp`
- `feature_as_of_timestamp`
- `event_timestamp`
- `season`
- `week`
- `game_id`
- `player_id`
- `source_player_id`
- `identity_status`
- `included_in_builder`
- `exclusion_reason`
- `missingness_policy`
- `censoring_policy`
- `future_information_risk`
- `post_outcome_information_risk`
- `safe_for_replay_now`
- `safe_for_experiment_now`

## Feature Families Covered First

- schedule next game / opponent / bye;
- draft capital for post-draft anchors only;
- weekly roster status only if frozen week snapshots exist;
- roster status only with event/as-of timestamps;
- availability denominator fields only with roster, schedule, snap, stat, and injury source timing.

## Hard Rules

- Current display safety does not imply replay safety.
- Historical snapshots must include extraction timestamp and source as-of timestamp.
- Future weeks, post-outcome rows, and post-anchor roster survival must be excluded.
- Unresolved identity rows must be excluded.
- Missing values remain `Not enough information`.
- Missing injury is not healthy.
- Missing snap or stat is not zero.
- Missing roster is not clean, active, inactive, off-roster, or safe.
- Schedule context is not recommendation, matchup strength, start/sit, playoff odds, or trade timing.

## Approval Boundary

The builder may produce review evidence. It may not approve replay, experiments, model input, training input, source truth, app wiring, probabilities, rankings, hidden sort, trade value, pick value, or recommendations.
