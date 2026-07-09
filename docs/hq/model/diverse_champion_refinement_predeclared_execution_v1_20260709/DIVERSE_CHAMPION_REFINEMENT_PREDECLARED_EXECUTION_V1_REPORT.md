# Diverse Champion Refinement Predeclared Execution V1 Report

## Verdict

`YELLOW_DIVERSE_CHAMPION_REFINEMENT_MIXED_RESULTS`

## Clear Answer

The review-only diverse champion refinement registered `136` fixed candidates before scoring and scored `136` candidates on the accepted Formula Data Mart substrate. The grid refined exactly the six approved seed neighborhoods. `136` refined candidates beat PYF overall. `0` refined candidates beat the prior full-Gauntlet best reference of `0.755`. `0` seed neighborhoods produced a material improvement over their seed reference.

## Preserved Reference Benchmarks

- PYF Spearman: `0.741`
- Prior best Gauntlet overall candidate: `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE`, Spearman `0.755`
- Prior best QB: `GAUNTLET_020_THREE_YEAR_55_30_15`
- Prior best RB: `GAUNTLET_109_ROBUST_WINSOR_THREE_60_10`
- Prior best WR: `GAUNTLET_016_THREE_YEAR_75_20_5`
- Prior best TE: `GAUNTLET_016_THREE_YEAR_75_20_5`
- Prior candidates beating PYF overall: `90`
- Effective distinct promising clusters: `6`

## Benchmark Scope

- Rows tested: `5518`
- Seasons: `2013-2025`
- Positions: `{'QB': 754, 'RB': 1429, 'TE': 1211, 'WR': 2124}`
- Review-only rows: `5518`
- Model-use allowed rows: `0`
- Production-approved rows: `0`

## Best Overall Refined Review-Only Candidate

`REFINE_007_OVERALL_THREE_65_25_10_LATE_20` from `A_OVERALL_DECLINE_AGE_ROLE_REFINEMENT` produced Spearman `0.755` versus PYF `0.741` and prior Gauntlet best `0.755`.

## Best Refined Candidate By Position

- QB: `REFINE_015_OVERALL_THREE_55_30_15_LATE_20` Spearman `0.737` delta_vs_pyf `0.025`
- RB: `REFINE_004_OVERALL_THREE_70_20_10_LATE_30` Spearman `0.651` delta_vs_pyf `0.017`
- WR: `REFINE_004_OVERALL_THREE_70_20_10_LATE_30` Spearman `0.703` delta_vs_pyf `0.012`
- TE: `REFINE_001_OVERALL_THREE_70_20_10_LATE_0` Spearman `0.719` delta_vs_pyf `0.018`

## Guardrails

- Sparse-history slice rows reviewed: `136` candidate-slice rows
- Low-games slice rows reviewed: `136` candidate-slice rows
- Prior-decline slice rows reviewed: `136` candidate-slice rows
- Age/lifecycle slice rows reviewed: `272` candidate-slice rows
- Role-archetype slice rows reviewed: `412` candidate-slice rows
- Most stable candidate: `REFINE_071_TE_THREE_80_15_5` with LOSO `13/13`

## Recommendation

Add missing data before more formula work.

## Gates Preserved

- Production/model-use remains blocked.
- Rankings integration remains blocked.
- Source promotion remains blocked.
- No app/runtime/model behavior changed.
- No production winner was selected.
