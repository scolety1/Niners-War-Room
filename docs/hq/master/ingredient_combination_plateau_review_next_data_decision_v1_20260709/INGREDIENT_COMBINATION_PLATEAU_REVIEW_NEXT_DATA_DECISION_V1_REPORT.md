# Ingredient Combination Plateau Review / Next Data Decision V1 Report

Verdict: `GREEN_NEXT_DATA_LANE_SELECTED_AFTER_PLATEAU_REVIEW`

Artifact path: `C:\NWR\Niners-War-Room-ingredient-combination-plateau-review-next-data-decision-v1-20260709\docs\hq\master\ingredient_combination_plateau_review_next_data_decision_v1_20260709`

Remote HQ verified: `b125be9ee73f1adc3487c1fa69ae954e8e49790f`

Prior rookie/draft commit verified: `f8978155f40b2cb9ba36b7b15947953cb6ae7542`

## Lanes Included

This review consolidates PFR RB broken tackles, ffopportunity / NGS autonomous V2, EPA/opportunity, receiving opportunity, snap/depth role, point-in-time injury availability, historical market/ADP gate, rookie/draft capital, age/lifecycle, role archetype, confidence cap, the full review-only Gauntlet, clustering audit, and diverse champion refinement.

## Plateau Decision

Ingredient-combination work has reached a current plateau with the available ingredients. The best full-history result is `0.758`, only about `+0.003` over the accepted `0.755` review-only plateau. The best broad-window result remains snap/depth at `0.763` across `2014-2025`. The strongest `0.790` results remain partial-window modern results from `2022-2025` and are not full-history comparable.

The evidence supports a data-upgrade pivot, not more same-ingredient formula tuning or ranking simulation.

## Best Scoreboards

- Full-history: `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_DEPTH_STABILITY_PCT100`, Spearman `0.758`, rows `5,518`, seasons `2013-2025`.
- Broad-window: `GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_SNAP_NOT_LOW_PCT100`, Spearman `0.763`, rows `5,122`, seasons `2014-2025`.
- Partial-window: `GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_FFOPPORTUNITY_PCT10`, Spearman `0.790`, rows `1,740`, seasons `2022-2025`.

## Next Lane

Recommended next lane: `Team Offensive Environment Sidecar V1`.

Reason: team/offensive environment is the best remaining public-data path with plausible accuracy upside, likely full-history or near-full-history coverage, and a clean lagged player-season join path through team-season context. It is more likely to add independent signal than another bounded combination pass with already-tested ingredients, and it has lower immediate leakage/source risk than market/ADP, FTN charting, participation/personnel/pressure, or paid data.

## Gates Preserved

- Production/model-use remains blocked.
- Rankings integration remains blocked.
- App/runtime changes remain blocked.
- Source promotion remains blocked.
- Review-only ranking simulation remains blocked.
- Push/merge was not performed.
- Current-best formula candidates are not approved for production use.
