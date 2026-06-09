# RB/WR Cross-Position Reality Check

Audit artifact: `C:\Dev\niners-war-room\local_exports\rb_wr_cross_position_reality_check.csv`

## Summary

- I found and patched one supported normalization bug: local baseline projections generated from recent imported LVE stats were being treated as independent expected-points evidence. They now neutralize `expected_lve_points_score` to 50, add `local_baseline_projection_not_independent`, and source coverage marks independent projection as a review gap.
- After that patch, the active preview is not overvaluing RBs versus WRs at the top. The named top order is Jefferson, Lamb, Chase, Amon-Ra/Brian Thomas, then Bijan/Gibbs. Kyren is no longer near RB1 and is flagged by injury/workload fragility.
- The cross-position board is still review-only because the player-stat production feed has 2023-2024 while role/depth/injury sources reach 2025, and no true independent projection/opportunity feed is imported yet.

## Named Player Snapshot

| player | rank | pos rank | model value | recent score | expected score | projection value | first-down/TD | injury | warnings |
|---|---:|---|---:|---:|---:|---:|---:|---:|---|
| Justin Jefferson | 1 | WR1 | 79.5 | 90.34 | 50.0 | 64.12 | 72.98 | 61.4 | local_baseline_projection_not_independent|missing_participation_proxy|stale_lve_scoring_source |
| CeeDee Lamb | 2 | WR2 | 78.06 | 92.96 | 50.0 | 65.04 | 77.38 | 34.76 | injury_risk|local_baseline_projection_not_independent|missing_participation_proxy|stale_lve_scoring_source |
| Ja'Marr Chase | 3 | WR3 | 77.09 | 90.25 | 50.0 | 64.09 | 73.61 | 51.86 | injury_risk|local_baseline_projection_not_independent|missing_participation_proxy|stale_lve_scoring_source |
| Amon-Ra St. Brown | 5 | WR5 | 76.61 | 86.4 | 50.0 | 62.74 | 74.99 | 43.08 | injury_risk|local_baseline_projection_not_independent|missing_participation_proxy|stale_lve_scoring_source |
| Brian Thomas Jr. | 8 | WR8 | 75.78 | 76.63 | 50.0 | 59.32 | 59.43 | 80.0 | local_baseline_projection_not_independent|missing_participation_proxy|stale_lve_scoring_source|young_nfl_bridge_prior_active |
| Bijan Robinson | 9 | RB1 | 75.12 | 90.33 | 50.0 | 64.12 | 75.54 | 86.36 | local_baseline_projection_not_independent|missing_participation_proxy|stale_lve_scoring_source|young_nfl_bridge_prior_active |
| Jahmyr Gibbs | 13 | RB2 | 70.73 | 96.84 | 50.0 | 66.39 | 75.43 | 69.04 | committee_risk|local_baseline_projection_not_independent|missing_participation_proxy|stale_lve_scoring_source|young_nfl_bridge_prior_active |
| De'Von Achane | 36 | RB6 | 66.13 | 85.36 | 50.0 | 62.37 | 62.17 | 59.18 | injury_risk|local_baseline_projection_not_independent|missing_participation_proxy|stale_lve_scoring_source|young_nfl_bridge_prior_active |
| Jaxon Smith-Njigba | 48 | WR39 | 62.29 | 49.76 | 50.0 | 49.92 | 42.07 | 72.68 | keeper_bubble|local_baseline_projection_not_independent|missing_participation_proxy|model_warning_keeper_fragility|route_role_fragility|stale_lve_scoring_source|young_nfl_bridge_prior_active |
| Kyren Williams | 49 | RB10 | 68.03 | 100.0 | 50.0 | 67.5 | 85.53 | 43.22 | injury_risk|keeper_bubble|local_baseline_projection_not_independent|missing_participation_proxy|model_warning_keeper_fragility|rb_workload_injury_fragility|stale_lve_scoring_source |
| Chase Brown | 94 | RB42 | 54.39 | 59.45 | 50.0 | 53.31 | 47.5 | 50.36 | committee_risk|injury_risk|keeper_bubble|local_baseline_projection_not_independent|missing_participation_proxy|model_warning_keeper_fragility|stale_lve_scoring_source|weak_chain_or_td_role|young_nfl_bridge_prior_active |

## Driver Conclusions

- Elite WRs are driven by target earning, route/role stability, age window, and strong recent LVE production. Their biggest blocker is not a formula bug; it is stale production and missing independent projections.
- Elite RBs are driven by recent LVE scoring, workload, first-down/TD fit, age, and injury durability. Bijan remains RB1, but the patched model keeps him behind the elite WR tier because his expected/opportunity feature is no longer double-counted from the same local baseline.
- Fragile RBs are being handled more safely now: Kyren has elite recent LVE production but carries injury/workload fragility and no independent projection; Achane carries injury/role review; Chase Brown is far lower due committee risk, weak chain/TD role, and young bridge review.
- Young bridge WRs remain high only when the imported evidence supports it. Brian Thomas is strong because production, target earning, age, and bridge prior align. JSN remains a review case because his current import window misses the likely 2025 breakout context.

## Proposed Fixture Before Any Future Formula Change

Do not apply a cross-position formula change until fresh/current production or an independent projection/opportunity feed is imported. The next fixture should assert this behavior: with current production and true independent projections loaded, elite target-earning WRs should remain above fragile role-only RBs, while elite young RBs with strong role, first-down fit, and durability should still clear mid-tier WRs.

## Decision Status

Rankings remain review-only. This audit corrected a normalization bug, but it did not clear the stale-production or missing-independent-projection blockers.
