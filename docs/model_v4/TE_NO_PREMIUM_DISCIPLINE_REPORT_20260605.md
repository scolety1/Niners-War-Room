# TE No-Premium Discipline Report

Date: 2026-06-05

Mode: review-only refinement prep.

Purpose: audit current-player TE values against the app's no-TE-premium context
before any formula work. This report is evidence only. It does not change TE
discipline, model weights, VORP, replacement formulas, pick baselines,
startup-slot conversion, generated outputs, or app state.

This report does not make trade, cut, keep, draft, buy, sell, defer, target, or
start/sit recommendations.

## Sources

Current-player source:

- Path:
  `local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv`
- Score column: `checkpoint_review_score`
- Lineage: `review_v4_current_player`
- Allowed use: `review_only_current_value_checkpoint`
- Blocked use: `do_not_use_as_final_ranking_or_roster_recommendation`

Owned-pick context source:

- Path:
  `local_exports/model_v4/pick_trade_defer/latest/niners_pick_inventory_review_rows.csv`
- Score column: `pick_value_review_score`
- Allowed use: `review_only_pick_inventory_not_trade_recommendation`
- Blocked use: `do_not_use_as_pick_trade_recommendation_or_offer`

Pick values are context only. They are not private-value inputs here and are not
trade-equivalence recommendations.

## TE Snapshot

- TE rows in current-player checkpoint: 11.
- TE rows with numeric current score: 10.
- TE rows with blank current score: 1.
- TE max score: `87.4776`.
- TE min numeric score: `13.7788`.
- TE mean numeric score: `37.6227`.
- TE median numeric score: `28.1813`.
- TE rows in top 20 by numeric current score: 1.
- TE rows in top 50 by numeric current score: 5.
- TE rows in bottom 20 by numeric current score: 5.
- TE rows with `no_premium_te` warning text: 7.
- TE rows with `capped_review_required`: 1.
- TE rows with partial or missing first-down warning text: 7.

## TE Rows With Nearby RB/WR Context

| Score Rank | File Row | Player | Team | Score | Confidence Cap | Confidence Status | Warning Flags | Nearest RB/WR Above | Nearest RB/WR Below |
|---:|---:|---|---|---:|---:|---|---|---|---|
| 1 | 61 | Trey McBride | ARI | 87.4776 | 0.88 | usable_with_confidence_cap | licensed_route_metrics_not_available; not_used_in_stats_first_value; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | none | Puka Nacua (WR 83.0486) |
| 25 | 65 | Travis Kelce | KC | 57.1755 | 0.88 | usable_with_confidence_cap | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | Drake London (WR 57.2578) | CeeDee Lamb (WR 56.2217) |
| 29 | 66 | Brock Bowers | LV | 50.0029 | 0.88 | usable_with_confidence_cap | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | Breece Hall (RB 53.4482) | Jaylen Waddle (WR 48.2068) |
| 37 | 67 | Jake Ferguson | DAL | 41.1387 | 0.88 | usable_with_confidence_cap | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | Keenan Allen (WR 41.6097) | Terry McLaurin (WR 39.3119) |
| 45 | 70 | George Kittle | SF | 32.0994 | 0.88 | usable_with_confidence_cap | licensed_route_metrics_not_available; not_used_in_stats_first_value; first_down_missing_confidence_cap; no_premium_te_small_gap_cap; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | Marvin Harrison Jr. (WR 32.3831) | Jakobi Meyers (WR 31.5686) |
| 62 | 71 | Sam LaPorta | DET | 24.2632 | 0.88 | usable_with_confidence_cap | licensed_route_metrics_not_available; not_used_in_stats_first_value; no_premium_te_small_gap_cap; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | Jayden Higgins (WR 25.2852) | Devin Singletary (RB 23.9309) |
| 63 | 74 | Oronde Gadsden II | LAC | 24.0072 | 0.88 | usable_with_confidence_cap | licensed_route_metrics_not_available; not_used_in_stats_first_value; first_down_missing_confidence_cap; no_premium_te_small_gap_cap; missing_or_review_first_down_evidence; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | Jayden Higgins (WR 25.2852) | Devin Singletary (RB 23.9309) |
| 65 | 72 | Brenton Strange | JAX | 23.1507 | 0.88 | usable_with_confidence_cap | licensed_route_metrics_not_available; not_used_in_stats_first_value; no_premium_te_small_gap_cap; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | Devin Singletary (RB 23.9309) | Jalen Coker (WR 22.2108) |
| 66 | 73 | Mark Andrews | BAL | 23.1327 | 0.88 | usable_with_confidence_cap | licensed_route_metrics_not_available; not_used_in_stats_first_value; partial_first_down_confidence_cap; no_premium_te_small_gap_cap; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | Devin Singletary (RB 23.9309) | Jalen Coker (WR 22.2108) |
| 71 | 76 | T.J. Hockenson | MIN | 13.7788 | 0.88 | usable_with_confidence_cap | licensed_route_metrics_not_available; not_used_in_stats_first_value; first_down_missing_confidence_cap; no_premium_te_replacement_level_cap; missing_or_review_route_target_snap_evidence; missing_lifecycle_or_role_shape_evidence | Luke McCaffrey (WR 16.2148) | Darrell Henderson (RB 9.6644) |

## Blank TE Row

| File Row | Player | Team | Score | Confidence Cap | Confidence Status | Warning Preview | Required Handling |
|---:|---|---|---|---:|---|---|---|
| 80 | Kenyon Sadiq | NYJ | blank | 0.82 | capped_review_required | missing_rotowire_player_stats; missing_stats_first_component_evidence; missing_vorp_anchor; ... | manual-review row; do not infer a primary score |

## TE vs Owned Pick Context

| TE | TE Score | Nearest Scored Owned Picks | Context Note |
|---|---:|---|---|
| Trey McBride | 87.4776 | 2026 1.04 at 90.4; 2026 1.03 at 93.6 | Near early first pick context; context only. |
| Travis Kelce | 57.1755 | 2026 2.08 at 58.6; 2026 2.04 at 71.4 | Very near 2026 2.08 by score; context only. |
| Brock Bowers | 50.0029 | 2026 2.08 at 58.6; 2026 2.04 at 71.4 | Below scored second-round pick context; context only. |
| Jake Ferguson | 41.1387 | 2026 2.08 at 58.6; 2026 2.04 at 71.4 | Below scored second-round pick context; context only. |
| George Kittle | 32.0994 | 2026 2.08 at 58.6; 2026 2.04 at 71.4 | Below scored second-round pick context; context only. |
| Sam LaPorta | 24.2632 | 2026 2.08 at 58.6; 2026 2.04 at 71.4 | No-premium small-gap cap prompt; context only. |
| Oronde Gadsden II | 24.0072 | 2026 2.08 at 58.6; 2026 2.04 at 71.4 | No-premium small-gap cap prompt; context only. |
| Brenton Strange | 23.1507 | 2026 2.08 at 58.6; 2026 2.04 at 71.4 | No-premium small-gap cap prompt; context only. |
| Mark Andrews | 23.1327 | 2026 2.08 at 58.6; 2026 2.04 at 71.4 | No-premium small-gap cap prompt; context only. |
| T.J. Hockenson | 13.7788 | 2026 2.08 at 58.6; 2026 2.04 at 71.4 | Replacement-level cap prompt; context only. |

The 2026 5.04 pick has no exact model baseline and remains manual-only. It is
not used as a scored comparison row.

## Discipline Observations

- `Trey McBride` is the highest numeric current-player score overall. In a
  no-TE-premium format, that is a primary human-review prompt for whether the TE
  context is clear and appropriately disclosed.
- `Travis Kelce`, `Brock Bowers`, and `Jake Ferguson` sit near notable RB/WR
  neighborhoods and should be reviewed for no-premium context clarity.
- `George Kittle`, `Sam LaPorta`, `Oronde Gadsden II`, `Brenton Strange`,
  `Mark Andrews`, and `T.J. Hockenson` carry explicit no-premium cap warning
  text.
- `Kenyon Sadiq` has a blank primary score and must remain a manual-review row.
- The spread between `Trey McBride` and the lower no-premium-capped TE cluster
  should be reviewed by a human before any formula proposal. This report does
  not say which side is correct.

## Non-Goals

- Do not change TE discipline from this report.
- Do not change model weights, VORP, replacement formulas, confidence caps, pick
  baselines, age curves, or startup-slot conversion from this report.
- Do not add market, ADP, rankings, projections, consensus, startup, or
  trade-calculator logic to private value.
- Do not use TE/pick neighborhoods as trade-equivalence recommendations.
- Do not convert any review label into a trade, cut, keep, draft, buy, sell,
  defer, target, or start/sit recommendation.
