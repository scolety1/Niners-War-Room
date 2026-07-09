# nflverse Snap Counts / Depth Chart Role Formula Mart Sidecar V1 Report

## Verdict

`GREEN_NFLVERSE_SNAP_DEPTH_ROLE_ADDS_REVIEW_ONLY_SIGNAL`

## Scope

This lane built a review-only snap-count and depth-chart role sidecar from public no-key nflverse parquet assets. It used feature season N to target season N+1 only. It did not mutate the canonical Formula Data Mart, canonical `local_exports`, app/runtime code, rankings, or production model behavior.

## Source And Sidecar

- Source families: public nflverse `snap_counts`, `depth_charts`, and `players` identity crosswalk.
- Feature seasons requested: `2012-2024`.
- Target seasons: `2013-2025`.
- Sidecar rows: `5518`.
- Snap/depth role join coverage: `5518 / 5518` or `100.0%`.
- Snap-count coverage: `5122 / 5122` or `100.0%`.
- Depth-chart coverage: `5518 / 5518` or `100.0%`.
- Source files hashed: `27`.

## Ingredients Loaded

- `snap_offensive_snaps`
- `snap_offensive_snap_share`
- `snap_games_with_offensive_snaps`
- `snap_low_snap_flag`
- `snap_not_low_snap_score`
- `snap_role_score`
- `snap_share_trend`
- `depth_primary_depth_rank`
- `depth_best_depth_rank`
- `depth_weeks_as_starter`
- `depth_weeks_as_backup`
- `depth_role_tier`
- `depth_role_change_flag`
- `depth_role_score`
- `depth_stability_score`
- `snap_depth_role_score`

## Tests

- Seed formulas: `19`.
- Total predeclared results: `940`.
- Component tests: `9`.
- Formula x ingredient tests: `513`.
- Ingredient combination tests: `418`.

## Best Results

- Best component test: `INGREDIENT_ONLY_SNAP_ROLE_SCORE` Spearman `0.692` PYF delta `-0.052`.
- Best formula x ingredient test: `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_SNAP_NOT_LOW_PCT100` Spearman `0.763` PYF delta `0.019`.
- Best ingredient combination: `GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_SNAPDEPTH_RECOPP_FFOP_PCT025_025_050` Spearman `0.789` PYF delta `0.011`.

## Top Review-Only Results

- `GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_SNAPDEPTH_RECOPP_FFOP_PCT025_025_050` Spearman `0.789` rows `1740` PYF delta `0.011` use `INTERACTION_ONLY`
- `GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_SNAPDEPTH_RECOPP_FFOP_PCT050_025_025` Spearman `0.789` rows `1740` PYF delta `0.010` use `INTERACTION_ONLY`
- `REFINE_007_OVERALL_THREE_65_25_10_LATE_20__PLUS_SNAPDEPTH_RECOPP_FFOP_PCT025_025_050` Spearman `0.789` rows `1740` PYF delta `0.010` use `INTERACTION_ONLY`
- `REFINE_007_OVERALL_THREE_65_25_10_LATE_20__PLUS_SNAPDEPTH_RECOPP_FFOP_PCT050_025_025` Spearman `0.789` rows `1740` PYF delta `0.010` use `INTERACTION_ONLY`
- `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_FFOP_PCT025_025` Spearman `0.788` rows `1740` PYF delta `0.010` use `INTERACTION_ONLY`
- `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_FFOP_PCT050_050` Spearman `0.788` rows `1740` PYF delta `0.010` use `INTERACTION_ONLY`
- `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_FFOP_PCT050_025` Spearman `0.788` rows `1740` PYF delta `0.009` use `INTERACTION_ONLY`
- `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_FFOP_PCT025_050` Spearman `0.788` rows `1740` PYF delta `0.010` use `INTERACTION_ONLY`
- `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_RECOPP_FFOP_PCT025_025_050` Spearman `0.788` rows `1740` PYF delta `0.010` use `INTERACTION_ONLY`
- `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_RECOPP_FFOP_PCT050_025_025` Spearman `0.788` rows `1740` PYF delta `0.009` use `INTERACTION_ONLY`
- `GAUNTLET_082_DECLINE_SMALL_HIGH_VOLUME_LATE_GUARD__PLUS_SNAPDEPTH_FFOP_PCT025_025` Spearman `0.788` rows `1740` PYF delta `0.009` use `INTERACTION_ONLY`
- `GAUNTLET_082_DECLINE_SMALL_HIGH_VOLUME_LATE_GUARD__PLUS_SNAPDEPTH_FFOP_PCT050_050` Spearman `0.788` rows `1740` PYF delta `0.009` use `INTERACTION_ONLY`
- `GAUNTLET_082_DECLINE_SMALL_HIGH_VOLUME_LATE_GUARD__PLUS_SNAPDEPTH_FFOP_PCT050_025` Spearman `0.788` rows `1740` PYF delta `0.009` use `INTERACTION_ONLY`
- `GAUNTLET_082_DECLINE_SMALL_HIGH_VOLUME_LATE_GUARD__PLUS_SNAPDEPTH_FFOP_PCT025_050` Spearman `0.788` rows `1740` PYF delta `0.010` use `INTERACTION_ONLY`
- `GAUNTLET_082_DECLINE_SMALL_HIGH_VOLUME_LATE_GUARD__PLUS_SNAPDEPTH_RECOPP_FFOP_PCT025_025_050` Spearman `0.788` rows `1740` PYF delta `0.010` use `INTERACTION_ONLY`

## Material Beat Of `.755`

- All result rows above `.755`: `145`.
- Broad lagged non-V2 snap/depth result rows above `.755`: `77`.

The strongest non-V2 snap-count rows are broad lagged results, not complete `2013-2025` results, because public 2012 snap counts are effectively unavailable and snap-only scores begin with target season `2014`. Any result using prior ffopportunity or NGS sidecars is partial-window only and cannot be used to claim a complete full-history `.755` plateau break.

## Ranking Simulation Decision

Review-only ranking simulation is not justified by this lane unless Master HQ separately approves a ranking-simulation design packet. Snap/depth role context remains review-only evidence.

## Gates Preserved

- Production/model-use remains blocked.
- Rankings integration remains blocked.
- App/runtime/model behavior changed: no.
- Push/merge: no.
- Source promotion: no.
- Canonical `local_exports` mutation: no.
