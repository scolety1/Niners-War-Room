# Receiving Opportunity Next Use Decision

Decision: `AVAILABLE_REVIEW_ONLY_INTERACTION_CONTEXT`.

Receiving opportunity was loaded cleanly from public nflverse/nflfastR play-by-play and is valid for lagged review-only Formula Mart sidecar use. The ingredient family may be used for bounded review-only interaction checks and slice/guardrail reporting. It is not approved for production/model-use, direct ranking input, hidden sort logic, or review-only ranking simulation.

Best component: `INGREDIENT_ONLY_REC_OPP_TARGETS` Spearman `0.685`.

Best formula x ingredient: `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_RECOPP_TARGETS_PCT025` Spearman `0.755`.

Best combination: `GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_RECOPP_WOPR_EPA_FFOP_PCT025_025_050` Spearman `0.790`.

Recommended next step: `Ingredient Combination Test Design V1` only if Master HQ wants a bounded design packet that compares full-history sidecars separately from partial-window ffop/NGS combinations. Otherwise continue the sidecar roadmap with FTN/snap-depth/injury/market gates before ranking simulation.
