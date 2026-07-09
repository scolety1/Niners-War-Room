# NWR Autonomous Ingredient Upgrade Sequence V2 Report

## Verdict

`GREEN_AUTONOMOUS_INGREDIENT_UPGRADE_SEQUENCE_COMPLETED_REVIEW_ONLY`

## Lanes Completed

- `ffopportunity Expected Fantasy Points Formula Mart Sidecar V1`
- `ffopportunity Component Test V1`
- `nflverse NGS Formula Mart Sidecar V1`
- `nflverse NGS Component Test V1`
- `Cluster Seed Formula x Ingredient Tests V1`
- `ffopportunity + NGS Ingredient Combination Tests V1`

## Ingredients Loaded

- `ffopportunity`: `2307` player-season sidecar rows from local `ep_weekly` parquet, source seasons `2021-2024`.
- `nflverse_ngs`: `1092` player-season sidecar rows from local NGS passing/receiving/rushing files, source seasons `2021-2024` with sparse `2024` NGS cache caveat.

## Ingredients Rejected Or Downgraded

- Full nflfastR/nflverse EPA/opportunity aggregates: not rebuilt in this run; recommended as a future source rebuild lane.
- Historical Market / ADP: parked behind nflverse sidecars because point-in-time/as-of safety is not proven.
- SportsDataIO: parked.
- PFR RB broken tackles: branch remains closed as main formula ingredient after prior no-incremental-signal result.

## Best Results

- Best component test: `INGREDIENT_ONLY_FFOP_XFP_TOTAL` Spearman `0.770` PYF delta `-0.009`.
- Best formula x ingredient test: `GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_FFOPPORTUNITY_PCT10` Spearman `0.790` PYF delta `0.011`.
- Best ingredient combination: `GAUNTLET_103_HYBRID_WR_TE_THREE_65_ROLE_AGE__PLUS_FFOP_NGS_PCT05_05` Spearman `0.758` PYF delta `0.016`.

## Top Review-Only Results

- `GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_FFOPPORTUNITY_PCT10` `0.790` rows `1740` use `ADDITIVE_CANDIDATE`
- `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_FFOPPORTUNITY_PCT10` `0.789` rows `1740` use `ADDITIVE_CANDIDATE`
- `GAUNTLET_082_DECLINE_SMALL_HIGH_VOLUME_LATE_GUARD__PLUS_FFOPPORTUNITY_PCT10` `0.789` rows `1740` use `ADDITIVE_CANDIDATE`
- `REFINE_007_OVERALL_THREE_65_25_10_LATE_20__PLUS_FFOPPORTUNITY_PCT10` `0.789` rows `1740` use `ADDITIVE_CANDIDATE`
- `GAUNTLET_103_HYBRID_WR_TE_THREE_65_ROLE_AGE__PLUS_FFOPPORTUNITY_PCT10` `0.782` rows `1056` use `ADDITIVE_CANDIDATE`
- `GAUNTLET_094_ROLE_WR_TE_TARGET_ROLE_REPORT__PLUS_FFOPPORTUNITY_PCT10` `0.782` rows `1056` use `ADDITIVE_CANDIDATE`
- `INGREDIENT_ONLY_FFOP_XFP_TOTAL` `0.770` rows `1740` use `GUARDRAIL_CONTEXT`
- `INGREDIENT_ONLY_FFOP_EXPECTED_FIRST_DOWNS` `0.768` rows `1740` use `DESCRIPTIVE_ONLY`
- `GAUNTLET_003_PRIOR_YEAR_PPG_BASELINE__PLUS_FFOPPORTUNITY_PCT10` `0.762` rows `1740` use `DESCRIPTIVE_ONLY`
- `GAUNTLET_103_HYBRID_WR_TE_THREE_65_ROLE_AGE__PLUS_NFLVERSE_NGS_PCT10` `0.759` rows `554` use `INTERACTION_ONLY`
- `GAUNTLET_103_HYBRID_WR_TE_THREE_65_ROLE_AGE__PLUS_FFOP_NGS_PCT05_05` `0.758` rows `554` use `INTERACTION_ONLY`
- `GAUNTLET_094_ROLE_WR_TE_TARGET_ROLE_REPORT__PLUS_NFLVERSE_NGS_PCT10` `0.758` rows `554` use `INTERACTION_ONLY`

## Material Beat Of `.755`

Partial-sample results above `.760`: `9`. These do not constitute a full-history material break of the `.755` plateau because the sidecars cover partial target seasons only.

## Ranking Simulation Decision

A review-only ranking simulation is not yet justified as a production-adjacent step. A narrower next lane is justified: rebuild/validate full nflfastR EPA/opportunity or run a second sidecar around the strongest partial ingredient with coverage expansion.

## CSV Outputs

- `C:\NWR\Niners-War-Room-autonomous-ingredient-upgrade-sequence-v2-20260709\docs\hq\model\nwr_autonomous_ingredient_upgrade_sequence_v2_20260709\AUTONOMOUS_ALL_RESULTS_REQUIRED_SCHEMA.csv`
- `C:\NWR\Niners-War-Room-autonomous-ingredient-upgrade-sequence-v2-20260709\docs\hq\model\nwr_autonomous_ingredient_upgrade_sequence_v2_20260709\AUTONOMOUS_COMPONENT_TEST_RESULTS.csv`
- `C:\NWR\Niners-War-Room-autonomous-ingredient-upgrade-sequence-v2-20260709\docs\hq\model\nwr_autonomous_ingredient_upgrade_sequence_v2_20260709\AUTONOMOUS_FORMULA_X_INGREDIENT_RESULTS.csv`
- `C:\NWR\Niners-War-Room-autonomous-ingredient-upgrade-sequence-v2-20260709\docs\hq\model\nwr_autonomous_ingredient_upgrade_sequence_v2_20260709\AUTONOMOUS_INGREDIENT_COMBINATION_RESULTS.csv`
- `C:\NWR\Niners-War-Room-autonomous-ingredient-upgrade-sequence-v2-20260709\docs\hq\model\nwr_autonomous_ingredient_upgrade_sequence_v2_20260709\FFOPPORTUNITY_EXPECTED_FANTASY_POINTS_REVIEW_ONLY_SIDECAR.csv`
- `C:\NWR\Niners-War-Room-autonomous-ingredient-upgrade-sequence-v2-20260709\docs\hq\model\nwr_autonomous_ingredient_upgrade_sequence_v2_20260709\NFLVERSE_NGS_REVIEW_ONLY_SIDECAR.csv`

## Gates Preserved

- Production/model-use remains blocked.
- Rankings integration remains blocked.
- App/runtime/model behavior changed: no.
- Push/merge: no.
- Source promotion: no.
