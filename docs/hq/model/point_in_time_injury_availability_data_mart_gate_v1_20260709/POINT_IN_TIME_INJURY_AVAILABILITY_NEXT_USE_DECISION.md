# Point-in-Time Injury Availability Next Use Decision

Decision: `AVAILABLE_REVIEW_ONLY_INTERACTION_CONTEXT`.

Point-in-time injury/availability data was loaded from public no-key nflverse assets and is valid only for lagged review-only Formula Mart sidecar use. It may support availability caveat review, guardrail/slice reporting, and bounded interaction checks. It is not approved for production/model-use, direct ranking input, hidden sort logic, source promotion, injury prediction, or review-only ranking simulation.

Best component: `INGREDIENT_ONLY_AVAIL_TWO_YEAR_DURABILITY_SCORE` Spearman `0.288`.

Best formula x ingredient: `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_AVAIL_CAVEAT_INVERSE_PCT100` Spearman `0.757`.

Best combination: `GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_AVAIL_FFOP_PCT025_025` Spearman `0.789`.

Recommended next step: `Historical Market / ADP Source Gate and Data Mart Join V1` after Master HQ review, because current public nflverse ingredient sidecars have mostly produced context/interactions rather than a full-history breakthrough suitable for ranking simulation.
