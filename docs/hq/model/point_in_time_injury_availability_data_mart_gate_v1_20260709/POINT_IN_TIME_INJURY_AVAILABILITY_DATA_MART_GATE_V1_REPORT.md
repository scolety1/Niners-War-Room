# Point-in-Time Injury Availability Data Mart Gate V1 Report

## Verdict

`YELLOW_POINT_IN_TIME_INJURY_AVAILABILITY_PARTIAL_WITH_CAVEATS`

## Scope

This lane built a review-only point-in-time injury/availability sidecar from public no-key nflverse `injuries` and `weekly_rosters` parquet assets. It used feature season N to target season N+1 only. It did not mutate the canonical Formula Data Mart, canonical `local_exports`, app/runtime code, rankings, or production model behavior.

## Source And Sidecar

- Source families: public nflverse `injuries` and `weekly_rosters`.
- Feature seasons requested: `2012-2024`.
- Target seasons: `2013-2025`.
- Sidecar rows: `5518`.
- Availability join coverage: `5490 / 5518` or `99.5%`.
- Source files hashed: `26`.

## Ingredients Loaded

- `avail_games_active`
- `avail_games_inactive`
- `avail_games_missed`
- `avail_active_pct`
- `avail_questionable_count`
- `avail_doubtful_count`
- `avail_out_count`
- `avail_probable_count`
- `avail_practice_dnp_count`
- `avail_practice_limited_count`
- `avail_injury_report_weeks`
- `avail_ir_pup_flag`
- `avail_prior_year_missed_games`
- `avail_two_year_missed_games`
- `avail_durability_score`
- `avail_report_clean_score`
- `avail_two_year_durability_score`
- `avail_availability_score`
- `avail_caveat_flag`
- `avail_caveat_inverse_score`

## Tests

- Seed formulas: `19`.
- Total predeclared results: `633`.
- Component tests: `6`.
- Formula x ingredient tests: `342`.
- Ingredient combination tests: `285`.

## Best Results

- Best component test: `INGREDIENT_ONLY_AVAIL_TWO_YEAR_DURABILITY_SCORE` Spearman `0.288` PYF delta `-0.452`.
- Best formula x ingredient test: `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_AVAIL_CAVEAT_INVERSE_PCT100` Spearman `0.757` PYF delta `0.016`.
- Best ingredient combination: `GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_AVAIL_FFOP_PCT025_025` Spearman `0.789` PYF delta `0.010`.

## Top Review-Only Results

- `GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_AVAIL_FFOP_PCT025_025` Spearman `0.789` rows `1740` PYF delta `0.010` use `INTERACTION_ONLY`
- `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_AVAIL_FFOP_PCT025_025` Spearman `0.788` rows `1740` PYF delta `0.009` use `INTERACTION_ONLY`
- `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_AVAIL_SNAPDEPTH_FFOP_PCT025_050_025` Spearman `0.788` rows `1740` PYF delta `0.009` use `INTERACTION_ONLY`
- `GAUNTLET_082_DECLINE_SMALL_HIGH_VOLUME_LATE_GUARD__PLUS_AVAIL_FFOP_PCT025_025` Spearman `0.788` rows `1740` PYF delta `0.009` use `INTERACTION_ONLY`
- `GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_AVAIL_FFOP_PCT050_050` Spearman `0.788` rows `1740` PYF delta `0.010` use `INTERACTION_ONLY`
- `GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_AVAIL_SNAPDEPTH_FFOP_PCT025_050_025` Spearman `0.788` rows `1740` PYF delta `0.010` use `INTERACTION_ONLY`
- `REFINE_007_OVERALL_THREE_65_25_10_LATE_20__PLUS_AVAIL_FFOP_PCT025_025` Spearman `0.788` rows `1740` PYF delta `0.010` use `INTERACTION_ONLY`
- `REFINE_007_OVERALL_THREE_65_25_10_LATE_20__PLUS_AVAIL_FFOP_PCT050_050` Spearman `0.788` rows `1740` PYF delta `0.010` use `INTERACTION_ONLY`
- `REFINE_007_OVERALL_THREE_65_25_10_LATE_20__PLUS_AVAIL_SNAPDEPTH_FFOP_PCT025_050_025` Spearman `0.788` rows `1740` PYF delta `0.009` use `INTERACTION_ONLY`
- `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_AVAIL_FFOP_PCT050_050` Spearman `0.787` rows `1740` PYF delta `0.009` use `INTERACTION_ONLY`
- `GAUNTLET_082_DECLINE_SMALL_HIGH_VOLUME_LATE_GUARD__PLUS_AVAIL_FFOP_PCT050_050` Spearman `0.787` rows `1740` PYF delta `0.009` use `INTERACTION_ONLY`
- `GAUNTLET_082_DECLINE_SMALL_HIGH_VOLUME_LATE_GUARD__PLUS_AVAIL_SNAPDEPTH_FFOP_PCT025_050_025` Spearman `0.787` rows `1740` PYF delta `0.009` use `INTERACTION_ONLY`
- `GAUNTLET_103_HYBRID_WR_TE_THREE_65_ROLE_AGE__PLUS_AVAIL_FFOP_PCT025_025` Spearman `0.781` rows `1056` PYF delta `0.005` use `INTERACTION_ONLY`
- `GAUNTLET_103_HYBRID_WR_TE_THREE_65_ROLE_AGE__PLUS_AVAIL_FFOP_PCT050_050` Spearman `0.781` rows `1056` PYF delta `0.006` use `INTERACTION_ONLY`
- `GAUNTLET_094_ROLE_WR_TE_TARGET_ROLE_REPORT__PLUS_AVAIL_FFOP_PCT050_050` Spearman `0.781` rows `1056` PYF delta `0.005` use `INTERACTION_ONLY`

## Comparability

- All result rows above `.755`: `43`.
- Full/broad lagged non-V2 rows above `.755`: `10`.
- Full/broad lagged non-V2 rows above snap/depth `.763`: `0`.
- Full-history-comparable rows tested: `116`.
- Broad-window-comparable rows tested: `114`.
- Partial-window rows tested: `95`.

Any result using prior ffopportunity or NGS sidecars is partial-window only and cannot be used to claim a complete full-history `.755` plateau break. Availability data is not injury prediction; it is a lagged historical availability context sidecar.

## Ranking Simulation Decision

Review-only ranking simulation is not justified by this lane. Injury/availability context remains review-only evidence unless Master HQ separately approves a ranking-simulation design packet.

## Gates Preserved

- Production/model-use remains blocked.
- Rankings integration remains blocked.
- App/runtime/model behavior changed: no.
- Push/merge: no.
- Source promotion: no.
- Canonical `local_exports` mutation: no.
