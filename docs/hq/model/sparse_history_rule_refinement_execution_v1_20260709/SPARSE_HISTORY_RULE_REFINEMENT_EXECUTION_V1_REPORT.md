# Sparse-History Rule Refinement Execution V1

## Verdict

`GREEN_SPARSE_HISTORY_REFINEMENT_FOUND_STRONG_MISS_REDUCTION`

## Scope

This is a review-only rule execution lane. It executed the 25 predeclared contract variants without adding variants, dynamic tuning, broad Formula Gauntlet, ranking simulation, production/model-use approval, app/runtime changes, source promotion, push/merge, or canonical `local_exports` writes.

Remote HQ verified: `b125be9ee73f1adc3487c1fa69ae954e8e49790f`.

Prior refinement contract commit verified: `3871cbf8854b28093bf361db4270681e45ccd236`.

## Execution Summary

Refined variants executed: `25`.

Windows tested: `full-history 2013-2025`, `broad-window 2014-2025`, and `partial-window 2022-2025`.

Best net miss-reduction variant: `REFINE_005_A_EARLY_ROLE_015` on `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_DEPTH_STABILITY_PCT100` / `full_history`, net miss reduction `16`, misses resolved `25`, new misses `9`.

Best false-negative reduction variant: `REFINE_005_A_EARLY_ROLE_015` with FN reduction `8`.

Best Spearman-improving variant: `REFINE_006_B_DRAFT_ROLE_050` with Spearman delta `0.004`.

Any variant met all pass/fail thresholds: `yes`.

Variants with unacceptable collateral flags: `43`.

## Classification Summary

- `REFINED_PROMISING_MISS_REDUCTION_RULE`: `REFINE_005_A_EARLY_ROLE_015, REFINE_005_B_EARLY_ROLE_025, REFINE_005_C_YEAR2_YEAR3_ONLY_025, REFINE_006_A_DRAFT_ROLE_025`
- `REFINED_MIXED_RULE`: `DIAG_001_A_ROLE_PROMO_025, DIAG_003_A_SNAP_GROWTH_025, DIAG_003_B_SNAP_GROWTH_STARTER_025, DIAG_008_A_POSITION_PROFILE_025, REFINE_002_B_PRIMARY_STARTER_050, REFINE_002_D_RB_WR_TE_STARTER_025, REFINE_005_D_EARLY_CLEAN_AVAIL_025, REFINE_005_E_EARLY_LOW_PYF_025, REFINE_006_B_DRAFT_ROLE_050, REFINE_006_C_ROUND1_ROLE_050, REFINE_006_D_DAY2_STARTER_025, REFINE_006_E_DRAFT_LOW_PYF_ROLE_050, REFINE_011_A_COMPOSITE_SMALL_025, REFINE_011_B_COMPOSITE_BALANCED_050, REFINE_011_C_COMPOSITE_STRICT_050, REFINE_011_E_COMPOSITE_POSITION_025`
- `REFINED_CONTEXT_ONLY_RULE`: `DIAG_001_B_ROLE_PROMO_STARTER_025, REFINE_002_A_DEPTH_STARTER_025`
- `REFINED_HARMFUL_RULE`: `DIAG_008_B_WR_TE_POSITION_PROFILE_025, REFINE_002_C_LOW_PYF_STARTER_050, REFINE_011_D_COMPOSITE_LOW_PYF_050`
- `REFINED_PARTIAL_WINDOW_ONLY_RULE`: `none`
- `REFINED_BLOCKED_OR_INVALID`: `none`

## Decision

Review-only ranking simulation remains not justified. Recommended next lane: `Sparse-History Refined Rule Review / Readiness Gate V1`.
