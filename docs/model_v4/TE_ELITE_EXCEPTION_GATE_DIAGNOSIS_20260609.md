# TE Elite Exception Gate Diagnosis - 2026-06-09

This diagnosis is readback-only. It does not change active Rankings or production formulas.

## Candidate TE Rows
| Player | Base Rank | Score | Trust | Component Read | Gate Diagnosis |
|---|---:|---:|---|---|---|
| Trey McBride | 1 | 87.4776 | Capped Score | vorp_anchor=100.0; route_target_role=91.5; first_down_yardage=95.3; yprr_target_efficiency=85.6; red_zone_secondary=97.2 | candidate exception: strong_private_te_role_receipts |
| Brock Bowers | 59 | 34.9344 | Capped Score | vorp_anchor=21.6; route_target_role=72.6; first_down_yardage=63.3; yprr_target_efficiency=69.3; red_zone_secondary=64.3 | candidate exception: strong_private_te_role_receipts |
| Kyle Pitts | 18 | 55.2691 | Capped Score | vorp_anchor=43.1; route_target_role=86.2; first_down_yardage=68.9; yprr_target_efficiency=68.9; red_zone_secondary=44.6 | candidate exception: strong_private_te_role_receipts |
| Travis Kelce | 25 | 50.9057 | Capped Score | vorp_anchor=33.6; route_target_role=83.3; first_down_yardage=71.3; yprr_target_efficiency=69.5; red_zone_secondary=63.5 | candidate exception: strong_private_te_role_receipts |
| Sam LaPorta | 149 | 15.4274 | Capped Score | vorp_anchor=0.0; route_target_role=55.4; first_down_yardage=55.5; yprr_target_efficiency=71.7; red_zone_secondary=34.8 | blocked: private_component_threshold_not_met |
| Mark Andrews | 162 | 14.0569 | Capped Score | vorp_anchor=0.0; route_target_role=60.6; first_down_yardage=34.5; yprr_target_efficiency=52.9; red_zone_secondary=65.9 | blocked: private_component_threshold_not_met |
| T.J. Hockenson | 164 | 13.7788 | Capped Score | vorp_anchor=0.0; route_target_role=63.0; first_down_yardage=42.9; yprr_target_efficiency=48.4; red_zone_secondary=37.8 | blocked: private_component_threshold_not_met |
| Jake Ferguson | 77 | 27.6842 | Capped Score | vorp_anchor=13.5; route_target_role=71.4; first_down_yardage=47.0; yprr_target_efficiency=62.4; red_zone_secondary=88.7 | blocked: private_component_threshold_not_met |
| George Kittle | 88 | 25.4179 | Capped Score | vorp_anchor=2.5; route_target_role=62.5; first_down_yardage=76.9; yprr_target_efficiency=81.8; red_zone_secondary=51.9 | blocked: private_component_threshold_not_met |
| Brenton Strange | 170 | 13.4585 | Capped Score | vorp_anchor=0.0; route_target_role=52.6; first_down_yardage=44.2; yprr_target_efficiency=58.3; red_zone_secondary=30.3 | blocked: private_component_threshold_not_met |
| Tucker Kraft | 156 | 14.7059 | Capped Score | vorp_anchor=0.0; route_target_role=55.7; first_down_yardage=49.0; yprr_target_efficiency=82.3; red_zone_secondary=41.3 | blocked: private_component_threshold_not_met |

## Answers
1. Available private TE evidence includes VORP anchor, route/target role, first-down/yardage, YPRR/target efficiency, red-zone context, confidence cap, trust status, and warning flags.
2. v1 over-compressed the top TE band by applying a broad no-premium cap without preserving enough elite-exception lift for rows with strong private role and production receipts.
3. TE exception candidates should be rows with strong route/target, first-down, and efficiency receipts, acceptable confidence, and no source/identity repair blocker.
4. Age/status warnings should cap or block exception treatment for veteran/status-risk TEs in the stricter variants.
5. Route/target/first-down/role components are available for the inspected TE rows, but warning flags still require human review.
6. Rows with replacement-level discipline or missing source/trust receipts should remain capped until source cleanup or additional private evidence exists.
7. A source-safe gate can use only private component receipts, confidence/trust, and warning flags. It must not use market rank, league rank, ADP, projections, or public rankings.
