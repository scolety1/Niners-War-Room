# JSN vs Tee Source Investigation

Rankings remain review-only. No formula weights were changed.

## Finding

The active data supports Tee over JSN only within the currently imported player-stat window, but that window is incomplete for a May 2026 decision: player stats contain 2023-2024 only, while snap/depth/injury sources already contain 2025. I patched the normalization pipeline to mark this as `stale_lve_scoring_source`, and source coverage now shows production as review for both players.

## Normalized Comparison

| Feature | JSN | Tee | Edge |
|---|---:|---:|---|
| recent LVE scoring | 49.76 | 68.64 | Tee |
| projection value | 52.21 | 67.31 | Tee |
| target earning | 70.25 | 82.23 | Tee |
| route role | 50.00 | 50.00 | push |
| role security | 59.43 | 59.42 | JSN |
| first-down/TD fit | 42.07 | 57.63 | Tee |
| efficiency | 38.65 | 49.92 | Tee |
| age curve | 94.00 | 94.00 | push |
| injury durability | 72.68 | 0.00 | JSN |

## Raw Season Snapshot

| Player | Season | Stat weeks | Calc LVE PPG | Targets | TPG | Rec yards | Rec TD | Rec FD | Avg target share | Avg snap % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Jaxon Smith-Njigba | 2023 | 17 | 5.32 | 93.0 | 5.47 | 628.0 | 4.0 | 29.0 | 0.175 | 64.8 |
| Jaxon Smith-Njigba | 2024 | 17 | 9.61 | 137.0 | 8.06 | 1130.0 | 6.0 | 55.0 | 0.238 | 86.4 |
| Jaxon Smith-Njigba | 2025 | 0 | n/a | 0 | n/a | 0 | 0 | 0 | n/a | 77.4 |
| Tee Higgins | 2023 | 12 | 8.23 | 76.0 | 6.33 | 656.0 | 5.0 | 33.0 | 0.176 | 73.8 |
| Tee Higgins | 2024 | 12 | 12.36 | 109.0 | 9.08 | 911.0 | 10.0 | 48.0 | 0.261 | 79.1 |
| Tee Higgins | 2025 | 0 | n/a | 0 | n/a | 0 | 0 | 0 | n/a | 80.9 |

## Receipt Drivers

- JSN: private_lve_value:dynasty_hold_value 64.25*58=37.265; private_lve_value:win_now_value 56.57*42=23.7594; dynasty_hold_value:age_curve 94.0*18=16.92; dynasty_hold_value:target_earning_stability 70.25*24=16.86; win_now_value:target_earning_stability 70.25*20=14.05; dynasty_hold_value:route_role 63.22*18=11.3796; win_now_value:role_security 59.43*18=10.6974; win_now_value:route_role 63.22*14=8.8508
- Tee: private_lve_value:dynasty_hold_value 71.45*58=41.441; private_lve_value:win_now_value 68.45*42=28.749; dynasty_hold_value:target_earning_stability 82.23*24=19.7352; dynasty_hold_value:age_curve 94.0*18=16.92; win_now_value:target_earning_stability 82.23*20=16.446; dynasty_hold_value:route_role 74.0*18=13.32; win_now_value:role_security 59.42*18=10.6956; win_now_value:route_role 74.0*14=10.36

## Decision

- Do not treat Tee > JSN as a final model conclusion yet.
- Within 2023-2024 imported scoring, Tee has the edge in LVE PPG, target earning, efficiency, and first-down/TD fit. JSN has the injury/age/young-prior profile edge.
- The source data is incomplete for the apparent 2025 context; this is now explicitly flagged as `stale_lve_scoring_source`.
- Next data fix is to import a player-stat source that includes the latest completed season, or accept that the app is using 2023-2024 production only.
- Formula unchanged.
