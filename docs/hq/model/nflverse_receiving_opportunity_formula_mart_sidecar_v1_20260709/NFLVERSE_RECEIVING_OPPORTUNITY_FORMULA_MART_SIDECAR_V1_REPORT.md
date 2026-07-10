# nflverse Receiving Opportunity Formula Mart Sidecar V1 Report

## Verdict

`YELLOW_NFLVERSE_RECEIVING_OPPORTUNITY_PARTIAL_WITH_CAVEATS`

## Scope

This lane built a review-only receiving opportunity sidecar from local public no-key nflfastR play-by-play parquet files and tested it with the top-3-per-cluster seed policy. It used lagged feature season N to target season N+1 only. It did not mutate the canonical Formula Data Mart, canonical `local_exports`, app/runtime code, rankings, or production model behavior.

## Source And Sidecar

- Source family: public nflverse/nflfastR `play_by_play_YYYY.parquet`.
- Source seasons: `2012-2024`.
- Target seasons: `2013-2025`.
- Sidecar rows: `5518`.
- Rows with prior receiving targets: `4663`.
- True-zero/no-target rows with source season available: `855`.
- Receiving opportunity join coverage: `5518 / 5518` or `100.0%`.
- Source files hashed: `13`.

## Ingredients Loaded

- `rec_opp_targets`
- `rec_opp_target_share`
- `rec_opp_air_yards`
- `rec_opp_air_yards_share`
- `rec_opp_wopr`
- `rec_opp_racr`
- `rec_opp_pacr`
- `rec_opp_yac`
- `rec_opp_receiving_first_downs`
- `rec_opp_receiving_epa`

## Tests

- Seed formulas: `19`.
- Total predeclared results: `884`.
- Component tests: `10`.
- Formula x ingredient tests: `570`.
- Ingredient combination tests: `304`.

## Best Results

- Best component test: `INGREDIENT_ONLY_REC_OPP_TARGETS` Spearman `0.685` PYF delta `-0.056`.
- Best formula x ingredient test: `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_RECOPP_TARGETS_PCT025` Spearman `0.755` PYF delta `0.013`.
- Best ingredient combination: `GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_RECOPP_WOPR_EPA_FFOP_PCT025_025_050` Spearman `0.790` PYF delta `0.011`.

## Top Review-Only Results

- `GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_RECOPP_WOPR_EPA_FFOP_PCT025_025_050` Spearman `0.790` rows `1736` PYF delta `0.011` use `INTERACTION_ONLY`
- `GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_RECOPP_WOPR_EPA_FFOP_PCT050_025_025` Spearman `0.790` rows `1736` PYF delta `0.011` use `INTERACTION_ONLY`
- `REFINE_007_OVERALL_THREE_65_25_10_LATE_20__PLUS_RECOPP_WOPR_EPA_FFOP_PCT025_025_050` Spearman `0.790` rows `1736` PYF delta `0.011` use `INTERACTION_ONLY`
- `REFINE_007_OVERALL_THREE_65_25_10_LATE_20__PLUS_RECOPP_WOPR_EPA_FFOP_PCT050_025_025` Spearman `0.790` rows `1736` PYF delta `0.011` use `INTERACTION_ONLY`
- `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_RECOPP_WOPR_FFOP_PCT050_050` Spearman `0.789` rows `1740` PYF delta `0.011` use `INTERACTION_ONLY`
- `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_RECOPP_WOPR_FFOP_PCT050_025` Spearman `0.789` rows `1740` PYF delta `0.010` use `INTERACTION_ONLY`
- `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_RECOPP_WOPR_EPA_FFOP_PCT025_025_050` Spearman `0.789` rows `1736` PYF delta `0.011` use `INTERACTION_ONLY`
- `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_RECOPP_WOPR_EPA_FFOP_PCT050_025_025` Spearman `0.789` rows `1736` PYF delta `0.010` use `INTERACTION_ONLY`
- `GAUNTLET_082_DECLINE_SMALL_HIGH_VOLUME_LATE_GUARD__PLUS_RECOPP_WOPR_FFOP_PCT050_050` Spearman `0.789` rows `1740` PYF delta `0.010` use `INTERACTION_ONLY`
- `GAUNTLET_082_DECLINE_SMALL_HIGH_VOLUME_LATE_GUARD__PLUS_RECOPP_WOPR_FFOP_PCT050_025` Spearman `0.789` rows `1740` PYF delta `0.010` use `INTERACTION_ONLY`
- `GAUNTLET_082_DECLINE_SMALL_HIGH_VOLUME_LATE_GUARD__PLUS_RECOPP_WOPR_EPA_FFOP_PCT025_025_050` Spearman `0.789` rows `1736` PYF delta `0.010` use `INTERACTION_ONLY`
- `GAUNTLET_082_DECLINE_SMALL_HIGH_VOLUME_LATE_GUARD__PLUS_RECOPP_WOPR_EPA_FFOP_PCT050_025_025` Spearman `0.789` rows `1736` PYF delta `0.010` use `INTERACTION_ONLY`
- `GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_RECOPP_WOPR_FFOP_PCT025_025` Spearman `0.789` rows `1740` PYF delta `0.010` use `INTERACTION_ONLY`
- `GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_RECOPP_WOPR_FFOP_PCT050_050` Spearman `0.789` rows `1740` PYF delta `0.011` use `INTERACTION_ONLY`
- `GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_RECOPP_WOPR_FFOP_PCT050_025` Spearman `0.789` rows `1740` PYF delta `0.011` use `INTERACTION_ONLY`

## Material Beat Of `.755`

- All result rows above `.755`: `70`.
- Full-history-comparable receiving/EPA-only result rows above `.755`: `0`.

Any result using prior ffopportunity or NGS sidecars is partial-window only and cannot be used to claim a full-history `.755` plateau break.

## Ranking Simulation Decision

Review-only ranking simulation is not justified by this lane. Receiving opportunity is useful as review-only interaction/slice context only unless Master HQ separately approves a later simulation after full-history comparability and ranking-specific gates are satisfied.

## Gates Preserved

- Production/model-use remains blocked.
- Rankings integration remains blocked.
- App/runtime/model behavior changed: no.
- Push/merge: no.
- Source promotion: no.
- Canonical `local_exports` mutation: no.
