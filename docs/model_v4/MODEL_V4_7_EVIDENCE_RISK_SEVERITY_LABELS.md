# Model v4.7 Evidence Risk Severity Labels

## Goal

Patch the non-blocking v4.6 audit concern that offline Evidence Risk review still required decoding raw risk codes.

## Changes

- Added `severity_label` to `source_risk_player_summary_rows.csv`.
- Added `severity_rank` to support sorting.
- Added `human_review_priority` with short plain-English next-review guidance.
- Updated Draft Room Evidence & Risk summary display to show Severity and Priority.
- Preserved raw `worst_source_risk_level` codes.

## Severity Map

| Raw Risk Code | Severity | Rank |
|---|---|---:|
| `red_manual_review` | High | 1 |
| `orange_source_limited` | Medium-high | 2 |
| `yellow_partial` | Medium | 3 |
| `gray_missing` | Manual context | 4 |
| `green_complete` | Low | 5 |

## Safety

This patch changes readability only. It does not alter formulas, scores, rankings, active app state, My Team, War Board, readiness gates, app promotion, or recommendations. Missing data remains missing, and raw audit codes remain available.
