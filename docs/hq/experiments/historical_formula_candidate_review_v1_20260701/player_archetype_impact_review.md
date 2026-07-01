# Player Archetype Impact Review

Diagnostic archetypes are derived only for review. They are not formula inputs.
- `holdout` / `target_volume_receiver`: rows `50`, mean error improvement `11.769667`.
- `holdout` / `high_prior_scoring_low_usage_adjustment`: rows `39`, mean error improvement `6.394316`.
- `holdout` / `qb_prior_points_and_passing_context`: rows `126`, mean error improvement `1.720185`.
- `holdout` / `rush_volume_back`: rows `93`, mean error improvement `1.286703`.
- `holdout` / `balanced_usage_profile`: rows `239`, mean error improvement `0.998124`.
- `holdout` / `low_volume_prior_season`: rows `343`, mean error improvement `0.153231`.
- `validation` / `qb_prior_points_and_passing_context`: rows `130`, mean error improvement `5.567436`.
- `validation` / `target_volume_receiver`: rows `51`, mean error improvement `4.060882`.
- `validation` / `rush_volume_back`: rows `94`, mean error improvement `2.95984`.
- `validation` / `balanced_usage_profile`: rows `251`, mean error improvement `2.038944`.
- `validation` / `low_volume_prior_season`: rows `355`, mean error improvement `0.354601`.
- `validation` / `high_prior_scoring_low_usage_adjustment`: rows `31`, mean error improvement `0.343333`.

The largest positive archetypes generally align with target or rush volume profiles. Regressions should be reviewed in the sample CSV before any future production discussion.
