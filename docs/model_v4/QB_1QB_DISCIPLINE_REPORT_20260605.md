# QB 1QB Discipline Report

Date: 2026-06-05

Mode: review-only refinement prep.

Purpose: audit current-player QB values against the app's 1QB/no-superflex
context before any formula work. This report is evidence only. It does not
change QB caps, model weights, VORP, replacement formulas, pick baselines,
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

Pick values are included only as context so the user can spot confusing
cross-surface neighborhoods. They are not private-value inputs here and are not
trade-equivalence recommendations.

## QB Snapshot

- QB rows in current-player checkpoint: 9.
- QB rows with numeric current score: 8.
- QB rows with blank current score: 1.
- QB rows in top 20 by numeric current score: 3.
- QB rows in bottom 15 by numeric current score: 3.
- QB rows with `one_qb` warning text: 5.
- QB rows with `qb_rushing_age` warning text: 3.
- QB rows with `capped_review_required`: 1.

## QB Rows With Nearby RB/WR Context

| Score Rank | File Row | Player | Team | Score | Confidence Cap | Confidence Status | Warning Flags | Nearest RB/WR Above | Nearest RB/WR Below |
|---:|---:|---|---|---:|---:|---|---|---|---|
| 5 | 62 | Josh Allen | BUF | 80.3133 | 0.88 | usable_with_confidence_cap | qb_rushing_age_caution_active; missing_or_review_route_target_snap_evidence | Christian McCaffrey (RB 82.8329) | Jonathan Taylor (RB 80.1465) |
| 13 | 63 | Jalen Hurts | PHI | 65.0980 | 0.88 | usable_with_confidence_cap | missing_or_review_route_target_snap_evidence | Derrick Henry (RB 66.2156) | James Cook (RB 63.7724) |
| 16 | 64 | Patrick Mahomes | KC | 61.5482 | 1.0 | high_confidence_metadata | partial_first_down_confidence_cap; qb_rushing_age_caution_active | George Pickens (WR 62.9783) | Kyren Williams (RB 61.1255) |
| 38 | 68 | Lamar Jackson | BAL | 40.3535 | 1.0 | high_confidence_metadata | one_qb_small_vorp_gap_cap; qb_rushing_age_caution_active | Keenan Allen (WR 41.6097) | Terry McLaurin (WR 39.3119) |
| 51 | 69 | Daniel Jones | IND | 31.3120 | 0.8 | capped_review_required | team_mismatch_or_missing_model_team; one_qb_small_vorp_gap_cap; identity_review_cap; partial_or_quarantined_join_cap | Romeo Doubs (WR 31.3334) | Jerry Jeudy (WR 31.1199) |
| 68 | 75 | Brock Purdy | SF | 21.3779 | 0.88 | usable_with_confidence_cap | one_qb_pocket_mid_qb_cap; missing_or_review_route_target_snap_evidence | Jalen Coker (WR 22.2108) | Amari Cooper (WR 20.7072) |
| 72 | 77 | Joe Burrow | CIN | 11.9641 | 0.88 | usable_with_confidence_cap | one_qb_pocket_mid_qb_cap; missing_or_review_route_target_snap_evidence | Luke McCaffrey (WR 16.2148) | Darrell Henderson (RB 9.6644) |
| 74 | 78 | Jayden Daniels | WAS | 8.9902 | 1.0 | high_confidence_metadata | one_qb_replacement_level_qb_cap | Darrell Henderson (RB 9.6644) | Kaleb Johnson (RB 3.0698) |

## Blank QB Row

| File Row | Player | Team | Score | Confidence Cap | Confidence Status | Warning Preview | Required Handling |
|---:|---|---|---|---:|---|---|---|
| 79 | Fernando Mendoza | LVR | blank | 0.82 | capped_review_required | missing_rotowire_player_stats; missing_stats_first_component_evidence; missing_vorp_anchor; ... | manual-review row; do not infer a primary score |

## QB vs Owned Pick Context

| QB | QB Score | Nearest Scored Owned Picks | Context Note |
|---|---:|---|---|
| Josh Allen | 80.3133 | 2026 2.04 at 71.4; 2026 1.04 at 90.4 | Between scored early/mid pick bands; context only. |
| Jalen Hurts | 65.0980 | 2026 2.04 at 71.4; 2026 2.08 at 58.6 | Near the second-round pick context band; context only. |
| Patrick Mahomes | 61.5482 | 2026 2.08 at 58.6; 2026 2.04 at 71.4 | Very near 2026 2.08 by score; context only. |
| Lamar Jackson | 40.3535 | 2026 2.08 at 58.6; 2026 2.04 at 71.4 | Below scored owned second-round picks; context only. |
| Daniel Jones | 31.3120 | 2026 2.08 at 58.6; 2026 2.04 at 71.4 | Below scored owned second-round picks; context only. |
| Brock Purdy | 21.3779 | 2026 2.08 at 58.6; 2026 2.04 at 71.4 | Below scored owned second-round picks; context only. |
| Joe Burrow | 11.9641 | 2026 2.08 at 58.6; 2026 2.04 at 71.4 | Bottom-band 1QB context prompt; context only. |
| Jayden Daniels | 8.9902 | 2026 2.08 at 58.6; 2026 2.04 at 71.4 | Bottom-band 1QB replacement-level cap prompt; context only. |

The 2026 5.04 pick has no exact model baseline and remains manual-only. It is
not used as a scored comparison row.

## Discipline Observations

- `Josh Allen`, `Jalen Hurts`, and `Patrick Mahomes` appear inside the top 20 by
  numeric current score. In a 1QB/no-superflex format, that is a human-review
  prompt for whether top-end QB rows are visually and contextually clear.
- `Lamar Jackson`, `Brock Purdy`, `Joe Burrow`, and `Jayden Daniels` carry
  explicit 1QB cap warnings and sit well below the top QB cluster.
- `Daniel Jones` carries both 1QB cap text and identity/team review warnings.
- `Jayden Daniels` is a known legacy-vs-current spread sentinel from R04; the
  current checkpoint score here is `8.9902`, not legacy active-pack value.
- The spread between top QB rows and capped lower QB rows should be reviewed by
  a human before any formula proposal. This report does not say which side is
  correct.

## Non-Goals

- Do not change QB caps or weights from this report.
- Do not change VORP, replacement formulas, confidence caps, pick baselines, or
  startup-slot conversion from this report.
- Do not add market, ADP, rankings, projections, consensus, startup, or
  trade-calculator logic to private value.
- Do not use QB/pick neighborhoods as trade-equivalence recommendations.
- Do not convert any review label into a trade, cut, keep, draft, buy, sell,
  defer, target, or start/sit recommendation.
