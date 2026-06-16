# Build Sprint 5Q: Feature Legality Review

Status: `FEATURES_VALID_AFTER_RENAME`

Sprint 5Q audited leakage-sensitive features from the Sprint 5P internal baseline mechanics experiment. The review focused on `prior_nwr_ppg`, `prior_nwr_finish_rank`, and related prior-production features before any future modeling work continues.

This sprint did not train calibrated models, create app percentage values, create public/player-facing probabilities, create rankings, push, deploy, modify active app/ranking logic, or promote a model artifact.

## Inputs Reviewed

Sprint 5Q reviewed:

- Sprint 5N broader historical feature snapshots:
  - `local_exports/outcome_probability/sprint_5n_broader_historical_rebuild/broader_historical_feature_snapshots.csv`
- Sprint 5N label linkage:
  - `local_exports/outcome_probability/sprint_5n_broader_historical_rebuild/broader_historical_label_linkage.csv`
- Sprint 5P coefficient sanity output:
  - `local_exports/outcome_probability/sprint_5p_internal_baseline_experiment/feature_coefficient_sanity.csv`
- Sprint 5K historical availability policy:
  - `completed_prior_season_stats_available_feb15_v1`

The audited feature snapshots covered:

- Row family: `all_player_pre_week1`
- Target seasons: `2023`, `2024`
- Snapshot rows: `827`
- Valid snapshot legality rows: `827`
- Invalid snapshot legality rows: `0`

## Policy Applied

Sprint 5Q applied the Sprint 5K historical availability policy:

- Completed prior-season factual NWR stat components may use derived availability date `Y-02-15`.
- Pre-Week-1 prediction cutoff is `Y-09-01`.
- Only seasons completed before the target season may be used as features.
- Same-season final stats remain forbidden as preseason features.
- Target labels and future-window labels remain forbidden as features.
- Public fantasy totals are not allowed as labels or features.
- ADP, rankings, projections, market/trade values, prior fantasy draft history, and legacy `private_score` remain forbidden.
- Label supplement sources are label-layer only, not prediction-time features.

## Feature Lineage Findings

The Sprint 5P mechanics feature set used only completed prior-season facts and stable identity/context fields.

Legal with clearer naming:

- `prior_nwr_ppg`
- `prior_nwr_finish_rank`
- `prior_games_played`
- `prior_rushing_first_downs`
- `prior_receiving_first_downs`
- `prior_receptions`
- `prior_rushing_yards`
- `prior_receiving_yards`
- `prior_passing_yards`
- `experience_at_snapshot`

Already acceptable as context with manifest controls:

- `age_at_snapshot`
- `position`

Not present in Sprint 5P and requiring manual review if added later:

- `prior_nwr_total_points`
- prior-season label-like fields

Blocked for modeling:

- same-season final stats
- target-window labels
- future-window labels
- public fantasy totals
- label supplement sources as prediction features

## Sensitive Features

### `prior_nwr_ppg`

Classification: `allowed_with_renaming`

`prior_nwr_ppg` is legal for internal mechanics because it is derived from completed prior-season NWR scoring components, with derived availability before the target-season cutoff. It is not an imported public fantasy total.

Required rename:

- `prior_nwr_ppg` -> `prior_season_nwr_ppg`

Future use requires:

- derived availability check
- source season strictly before target season
- no imported fantasy totals
- position/context normalization review
- final leakage audit before production candidate use

### `prior_nwr_finish_rank`

Classification: `allowed_with_renaming`

`prior_nwr_finish_rank` is label-like, but it refers to a completed prior season and does not overlap the target window. It is legal only if it remains explicitly tied to the completed prior season.

Required rename:

- `prior_nwr_finish_rank` -> `prior_season_nwr_finish_rank`

Future use requires:

- derived availability check
- source season strictly before target season
- final leakage review
- position normalization review
- explicit distinction from same-year target labels

## Rename Recommendations

Required before future training:

- `prior_nwr_ppg` -> `prior_season_nwr_ppg`
- `prior_nwr_finish_rank` -> `prior_season_nwr_finish_rank`

Recommended before future training:

- `experience_at_snapshot` -> `experience_entering_season`
- `prior_games_played` -> `prior_completed_season_games`
- `prior_passing_yards` -> `prior_completed_season_passing_yards`
- `prior_receiving_first_downs` -> `prior_completed_season_receiving_first_downs`
- `prior_receiving_yards` -> `prior_completed_season_receiving_yards`
- `prior_receptions` -> `prior_completed_season_receptions`
- `prior_rushing_first_downs` -> `prior_completed_season_rushing_first_downs`
- `prior_rushing_yards` -> `prior_completed_season_rushing_yards`

If `prior_nwr_total_points` is added later, recommended name:

- `prior_season_nwr_total_points`

## Future Model-Feature Policy

Future internal mechanics may continue using the audited prior completed-season features if:

- source season is strictly before target season
- derived availability date is on or before the prediction cutoff
- the feature is renamed or carries explicit completed-prior-season lineage metadata
- no public fantasy totals, rankings, projections, market values, or supplement label-only sources enter the feature payload

Future production candidate use remains blocked pending:

- final leakage audit
- explicit approval of NWR-derived prior scoring features
- position normalization review for `prior_season_nwr_ppg` and `prior_season_nwr_finish_rank`
- calibration/display gates

## Sprint 5P Validity Reassessment

Sprint 5P remains valid as internal mechanics.

Assessment:

- Aggregate diagnostics: `valid_as_internal_mechanics`
- `prior_nwr_ppg`: `valid_after_feature_rename`
- `prior_nwr_finish_rank`: `valid_after_feature_rename`
- prior completed-season counting stats: `valid_as_internal_mechanics`
- production/app readiness: `manual_review_required`

Sprint 5P is not invalidated by leakage because the audited feature lineage uses completed prior-season facts available before the target-season cutoff. The warning remains: these features must be renamed and carry lineage controls before future model work depends on them.

## Local Outputs

Sprint 5Q wrote local-only exports under:

`local_exports/outcome_probability/sprint_5q_feature_legality_review/`

Created exports:

- `feature_lineage_audit.csv`
- `feature_legality_classification.csv`
- `model_feature_policy.csv`
- `feature_rename_recommendations.csv`
- `sprint_5p_validity_reassessment.csv`
- `README_SPRINT_5Q.md`

## Verdict

Readiness verdict: `FEATURES_VALID_AFTER_RENAME`

Future internal modeling may continue only after the feature names and lineage metadata are made explicit. Production/app modeling remains blocked.

## Remaining Blockers Before App-Facing Calibrated Probabilities

- Rename or schema-version the ambiguous prior-season features.
- Carry derived availability metadata into future training rows.
- Complete final leakage audit for all model features.
- Add more seasons for validation/calibration support.
- Decide whether next-year outcomes remain excluded or wait for mature labels.
- Build calibration, confidence, and display gates.
- Obtain explicit HQ approval before saving or promoting any model artifact.

## Safety Confirmation

No app percentages, calibrated probabilities, player-facing probabilities, rankings, push, or deploy occurred.
