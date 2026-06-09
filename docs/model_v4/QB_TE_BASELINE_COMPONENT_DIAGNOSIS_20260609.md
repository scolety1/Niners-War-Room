# QB/TE Baseline Component Diagnosis - 2026-06-09

This diagnosis reads current component receipts only. It does not change formulas.

## QB Component Readback
### Top QB rows

| Player | Rank | Score | Main component read |
|---|---:|---:|---|
| Josh Allen | 5 | 80.3133 | vorp_anchor: contribution 45.0; rushing_separation: contribution 22.8568; passing_volume_security: contribution 9.8121; passing_production: contribution 7.5365 |
| Drake Maye | 8 | 77.0377 | vorp_anchor: contribution 38.1146; rushing_separation: contribution 18.4183; passing_volume_security: contribution 10.7351; passing_production: contribution 6.496 |
| Trevor Lawrence | 9 | 73.5624 | vorp_anchor: contribution 31.4059; rushing_separation: contribution 16.8853; passing_volume_security: contribution 13.3969; passing_production: contribution 6.4137 |
| Matthew Stafford | 19 | 55.0484 | vorp_anchor: contribution 25.8348; passing_volume_security: contribution 14.4523; passing_production: contribution 8.464; regression_context: contribution 4.9 |
| Caleb Williams | 33 | 47.1915 | vorp_anchor: contribution 19.126; rushing_separation: contribution 13.0335; passing_volume_security: contribution 12.294; passing_production: contribution 5.9971 |
| Justin Herbert | 37 | 43.9605 | rushing_separation: contribution 14.7081; passing_volume_security: contribution 12.9625; vorp_anchor: contribution 10.9067; passing_production: contribution 6.1758 |
| Jalen Hurts | 42 | 41.1499 | rushing_separation: contribution 18.8801; vorp_anchor: contribution 13.2215; passing_volume_security: contribution 9.1278; passing_production: contribution 6.9227 |
| Bo Nix | 43 | 40.4641 | passing_volume_security: contribution 13.6061; rushing_separation: contribution 12.3759; vorp_anchor: contribution 10.9067; passing_production: contribution 5.8752 |
### Low QB rows with review relevance

| Player | Rank | Score | Main component read |
|---|---:|---:|---|
| Shedeur Sanders | 228 | 5.0521 | rushing_separation: contribution 3.6776; passing_volume_security: contribution 3.2872; passing_production: contribution 1.746; regression_context: contribution 0.8575 |
| Michael Penix | 227 | 5.3338 | passing_volume_security: contribution 5.6846; rushing_separation: contribution 3.2575; passing_production: contribution 2.9058; vorp_anchor: contribution 0.0 |
| Kyler Murray | 225 | 6.1955 | passing_volume_security: contribution 5.1088; rushing_separation: contribution 4.8457; regression_context: contribution 2.5895; passing_production: contribution 2.1233 |
| Joe Burrow | 219 | 7.4662 | passing_volume_security: contribution 5.7255; passing_production: contribution 4.751; regression_context: contribution 3.551; rushing_separation: contribution 2.0413 |
| J.J. McCarthy | 217 | 7.5485 | rushing_separation: contribution 6.2216; passing_volume_security: contribution 4.8209; passing_production: contribution 2.2456; regression_context: contribution 1.0082 |
| Justin Fields | 210 | 8.7042 | rushing_separation: contribution 11.7852; passing_volume_security: contribution 4.8096; passing_production: contribution 2.0608; regression_context: contribution 1.9423 |
| Jayden Daniels | 208 | 8.9902 | rushing_separation: contribution 7.7199; passing_volume_security: contribution 3.9434; passing_production: contribution 3.1682; regression_context: contribution 2.1954 |
| Aaron Rodgers | 201 | 10.0345 | passing_volume_security: contribution 11.9973; passing_production: contribution 5.3906; regression_context: contribution 3.1444; rushing_separation: contribution 2.7388 |

## TE Component Readback
### Top TE rows

| Player | Rank | Score | Main component read |
|---|---:|---:|---|
| Trey McBride | 1 | 87.4776 | vorp_anchor: contribution 45.0; route_target_role: contribution 22.8768; first_down_yardage: contribution 14.2882; yprr_target_efficiency: contribution 8.5569 |
| Kyle Pitts | 18 | 55.2691 | route_target_role: contribution 21.5615; vorp_anchor: contribution 19.3774; first_down_yardage: contribution 10.3308; yprr_target_efficiency: contribution 6.8925 |
| Travis Kelce | 25 | 50.9057 | route_target_role: contribution 20.8353; vorp_anchor: contribution 15.0998; first_down_yardage: contribution 10.6961; yprr_target_efficiency: contribution 6.9524 |
| Hunter Henry | 38 | 43.0176 | route_target_role: contribution 19.02; vorp_anchor: contribution 14.4154; first_down_yardage: contribution 8.6651; yprr_target_efficiency: contribution 6.094 |
| Tyler Warren | 57 | 35.5372 | route_target_role: contribution 17.6767; vorp_anchor: contribution 13.4316; first_down_yardage: contribution 7.6951; yprr_target_efficiency: contribution 6.0834 |
| Harold Fannin | 58 | 35.367 | route_target_role: contribution 21.0011; vorp_anchor: contribution 11.25; first_down_yardage: contribution 7.8419; yprr_target_efficiency: contribution 7.83 |
| Brock Bowers | 59 | 34.9344 | route_target_role: contribution 18.1514; vorp_anchor: contribution 9.7101; first_down_yardage: contribution 9.4945; yprr_target_efficiency: contribution 6.9279 |
| Dalton Schultz | 64 | 33.5524 | route_target_role: contribution 20.4205; first_down_yardage: contribution 8.4279; vorp_anchor: contribution 7.443; yprr_target_efficiency: contribution 6.3466 |

## Diagnosis Answers
1. Top QBs are usually high when the VORP anchor normalizes near the top of the QB pool and rushing separation adds another large private component.
2. Low elite/market-relevant QBs appear tied to QB universe expansion, position max normalizers, lifecycle/role modifiers, and confidence/warning interaction rather than source quarantine.
3. Trey McBride is #1 because TE VORP anchor, route/target role, first-down/yardage, efficiency, and red-zone components all read as strong before the no-premium format question is applied.
4. Brock Bowers, Sam LaPorta, Mark Andrews, T.J. Hockenson, and Brenton Strange depend on the same TE component family, but their normalized anchors and confidence/lifecycle states vary sharply.
5. The issues look primarily like format-context and cross-position scaling candidates, with no current non-kicker source quarantine blocker.
6. Formula-candidate areas are QB 1QB compression, TE no-premium ceiling behavior, and QB/TE cross-position balance. Some player-level rows remain human football review issues.
7. The current component fields do not fully expose every denominator/normalizer step, so any later formula work needs shadow diagnostics before promotion.
