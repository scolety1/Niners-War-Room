# nflverse EPA / Opportunity Formula Mart Sidecar V1 Report

## Verdict

`YELLOW_NFLVERSE_EPA_OPPORTUNITY_PARTIAL_WITH_CAVEATS`

## Scope

This lane built a review-only EPA/opportunity sidecar from public no-key nflfastR play-by-play parquet files and tested it with the V3 top-3-per-cluster seed policy. It did not rerun the completed ffopportunity/NGS sidecar builds; prior V2 sidecar outputs were used only for bounded combination tests.

## Source And Sidecar

- Source family: public nflverse/nflfastR `play_by_play_YYYY.parquet`.
- Source seasons: `2012-2024`.
- Sidecar rows: `5360`.
- Target seasons covered: `2013-2025`.
- EPA join coverage: `5360 / 5518` or `97.1%`.
- Source files hashed: `13`.

## Tests

- Seed formulas: `19`.
- Total predeclared tests: `139`.
- Component tests: `6`.
- Formula x ingredient tests: `76`.
- Ingredient combination tests: `57`.

## Best Results

- Best component test: `INGREDIENT_ONLY_EPA_TOTAL` Spearman `0.510` PYF delta `-0.223`.
- Best formula x ingredient test: `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_EPA_TOTAL_PCT05` Spearman `0.747` PYF delta `0.015`.
- Best ingredient combination: `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_EPA_FFOP_PCT05_05` Spearman `0.789` PYF delta `0.011`.

## Top Review-Only Results

- `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_EPA_FFOP_PCT05_05` `0.789` rows `1736` use `INTERACTION_ONLY`
- `GAUNTLET_082_DECLINE_SMALL_HIGH_VOLUME_LATE_GUARD__PLUS_EPA_FFOP_PCT05_05` `0.789` rows `1736` use `INTERACTION_ONLY`
- `GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_EPA_FFOP_PCT05_05` `0.789` rows `1736` use `INTERACTION_ONLY`
- `REFINE_007_OVERALL_THREE_65_25_10_LATE_20__PLUS_EPA_FFOP_PCT05_05` `0.789` rows `1736` use `INTERACTION_ONLY`
- `GAUNTLET_103_HYBRID_WR_TE_THREE_65_ROLE_AGE__PLUS_EPA_FFOP_PCT05_05` `0.781` rows `1056` use `INTERACTION_ONLY`
- `GAUNTLET_094_ROLE_WR_TE_TARGET_ROLE_REPORT__PLUS_EPA_FFOP_PCT05_05` `0.781` rows `1056` use `INTERACTION_ONLY`
- `GAUNTLET_003_PRIOR_YEAR_PPG_BASELINE__PLUS_EPA_FFOP_PCT05_05` `0.764` rows `1736` use `DESCRIPTIVE_ONLY`
- `GAUNTLET_103_HYBRID_WR_TE_THREE_65_ROLE_AGE__PLUS_EPA_NGS_PCT05_05` `0.759` rows `554` use `INTERACTION_ONLY`
- `GAUNTLET_103_HYBRID_WR_TE_THREE_65_ROLE_AGE__PLUS_EPA_FFOP_NGS_PCT04_04_02` `0.759` rows `554` use `INTERACTION_ONLY`
- `GAUNTLET_094_ROLE_WR_TE_TARGET_ROLE_REPORT__PLUS_EPA_NGS_PCT05_05` `0.759` rows `554` use `INTERACTION_ONLY`
- `GAUNTLET_094_ROLE_WR_TE_TARGET_ROLE_REPORT__PLUS_EPA_FFOP_NGS_PCT04_04_02` `0.758` rows `554` use `INTERACTION_ONLY`
- `GAUNTLET_059_TE_THREE_65_25_10__PLUS_EPA_FFOP_PCT05_05` `0.755` rows `378` use `INTERACTION_ONLY`

## Material Beat Of `.755`

Rows above `.755`: `11`.

- EPA-only formula x ingredient rows above `.755`: `0`.
- Partial-window EPA + prior V2 sidecar combination rows above `.755`: `11`.

No EPA-only near-full-history-comparable result materially beat `.755`. The `.755+` rows are review-only partial-window combinations because they require prior V2 ffopportunity or NGS sidecars, whose target window is lagged `2022-2025`.

## Ranking Simulation Decision

Review-only ranking simulation is not justified by this lane. The only `.755+` results are partial-window combinations, not full-history-comparable evidence.

## Gates Preserved

- Production/model-use remains blocked.
- Rankings integration remains blocked.
- App/runtime/model behavior changed: no.
- Push/merge: no.
- Source promotion: no.
- Canonical `local_exports` mutation: no.
