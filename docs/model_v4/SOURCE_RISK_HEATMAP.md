# Source-Risk Heatmap

## Scope

This review-only heatmap shows where player value is evidence-supported and where it is fragile due to missing, partial, source-limited, or quarantined data.

## Export Shape

`source_risk_player_rows.csv` preserves module/context-level evidence rows for audit. A player can appear more than once there when separate evidence modules or contexts need separate risk tracking. `source_risk_player_summary_rows.csv` is the human-facing one-row-per-player export.

## Summary

| Entity Type | Risk Level | Count |
|---|---|---:|
| current_player | red_manual_review | 15 |
| current_player | yellow_partial | 62 |
| current_player | green_complete | 3 |
| rookie_prospect | red_manual_review | 1 |
| rookie_prospect | orange_source_limited | 119 |
| rookie_prospect | yellow_partial | 90 |
| rookie_prospect | green_complete | 1 |

## Player Summary Rows

| Player | Pos | Worst Risk | Biggest Risk | Raw Rows |
|---|---|---|---|---:|
| George Pickens | WR | red_manual_review | production:red_manual_review | 1 |
| Jaylen Waddle | WR | red_manual_review | production:red_manual_review | 1 |
| Stefon Diggs | WR | red_manual_review | production:red_manual_review | 1 |
| Kenneth Walker III | RB | red_manual_review | production:red_manual_review | 1 |
| Wan'Dale Robinson | WR | red_manual_review | production:red_manual_review | 1 |
| Keenan Allen | WR | red_manual_review | production:red_manual_review | 1 |
| David Montgomery | RB | red_manual_review | production:red_manual_review | 1 |
| Jakobi Meyers | WR | red_manual_review | production:red_manual_review | 1 |
| Tyreek Hill | WR | red_manual_review | production:red_manual_review | 1 |
| Romeo Doubs | WR | red_manual_review | production:red_manual_review | 1 |
| Daniel Jones | QB | red_manual_review | production:red_manual_review | 1 |
| Mike Evans | WR | red_manual_review | production:red_manual_review | 1 |
| Cooper Kupp | WR | red_manual_review | production:red_manual_review | 1 |
| Amari Cooper | WR | red_manual_review | production:red_manual_review | 1 |
| Jam Miller | RB | red_manual_review | production:red_manual_review | 1 |
| Darrell Henderson | RB | red_manual_review | production:red_manual_review | 1 |
| Jeremiyah Love | RB | orange_source_limited | athletic:orange_source_limited | 2 |
| Jalon Daniels | QB | orange_source_limited | athletic:orange_source_limited | 1 |
| Dae'Quan Wright | TE | orange_source_limited | athletic:orange_source_limited | 1 |
| Jordyn Tyson | WR | orange_source_limited | athletic:orange_source_limited | 2 |
| Makai Lemon | WR | orange_source_limited | athletic:orange_source_limited | 1 |
| Jaydn Ott | RB | orange_source_limited | athletic:orange_source_limited | 1 |
| Joe Fagnano | QB | orange_source_limited | athletic:orange_source_limited | 1 |
| Skyler Bell | WR | orange_source_limited | athletic:orange_source_limited | 1 |
| Sawyer Robertson | QB | orange_source_limited | athletic:orange_source_limited | 1 |

## Highest Risk Rows

| Player | Pos | Type | Risk | Biggest Risk |
|---|---|---|---|---|
| George Pickens | WR | current_player | red_manual_review | production:red_manual_review |
| Jaylen Waddle | WR | current_player | red_manual_review | production:red_manual_review |
| Stefon Diggs | WR | current_player | red_manual_review | production:red_manual_review |
| Kenneth Walker III | RB | current_player | red_manual_review | production:red_manual_review |
| Wan'Dale Robinson | WR | current_player | red_manual_review | production:red_manual_review |
| Keenan Allen | WR | current_player | red_manual_review | production:red_manual_review |
| David Montgomery | RB | current_player | red_manual_review | production:red_manual_review |
| Jakobi Meyers | WR | current_player | red_manual_review | production:red_manual_review |
| Tyreek Hill | WR | current_player | red_manual_review | production:red_manual_review |
| Romeo Doubs | WR | current_player | red_manual_review | production:red_manual_review |
| Daniel Jones | QB | current_player | red_manual_review | production:red_manual_review |
| Mike Evans | WR | current_player | red_manual_review | production:red_manual_review |
| Cooper Kupp | WR | current_player | red_manual_review | production:red_manual_review |
| Amari Cooper | WR | current_player | red_manual_review | production:red_manual_review |
| Jam Miller | RB | rookie_prospect | red_manual_review | production:red_manual_review |
| Darrell Henderson | RB | current_player | red_manual_review | production:red_manual_review |
| Jeremiyah Love | RB | rookie_prospect | orange_source_limited | athletic:orange_source_limited |
| Jalon Daniels | QB | rookie_prospect | orange_source_limited | athletic:orange_source_limited |
| Dae'Quan Wright | TE | rookie_prospect | orange_source_limited | athletic:orange_source_limited |
| Jordyn Tyson | WR | rookie_prospect | orange_source_limited | athletic:orange_source_limited |
| Makai Lemon | WR | rookie_prospect | orange_source_limited | athletic:orange_source_limited |
| Jaydn Ott | RB | rookie_prospect | orange_source_limited | athletic:orange_source_limited |
| Joe Fagnano | QB | rookie_prospect | orange_source_limited | athletic:orange_source_limited |
| Skyler Bell | WR | rookie_prospect | orange_source_limited | athletic:orange_source_limited |
| Sawyer Robertson | QB | rookie_prospect | orange_source_limited | athletic:orange_source_limited |
