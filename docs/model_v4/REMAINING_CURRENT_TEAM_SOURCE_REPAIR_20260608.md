# Remaining Current Team Source Repair - 2026-06-08

This pass resolves or formally quarantines the remaining named current-team source gaps in Dynasty Rankings. It does not tune formulas, change NWR scores, modify ranking math, use market/league/legacy values, or touch the Decision Board.

## Local Sources Searched

- Active pack `fact_rosters.csv` `nfl_team`.
- Active pack `fact_official_rankings.csv` `nfl_team`.
- Active pack `dim_players.csv` `nfl_team`.
- Normalized local RotoWire team/status rows.
- Derived full-board `full_player_board_value_review_rows.csv` `nfl_team`.
- Existing identity repair audit receipts.
- Broader local CSV/export scan for named players. Historical/component team hits were treated as context-only unless they came from the active current-team precedence above.

## Summary

| Metric | Count |
| --- | ---: |
| named rows | 14 |
| named non-kicker targets | 12 |
| named non-kicker rows resolved | 3 |
| named non-kicker rows still quarantined | 9 |
| intentionally hidden kickers | 1 |

## Status Counts

| Repair status | Count |
| --- | ---: |
| current_status_verified_no_team | 9 |
| intentionally_hidden_kicker | 1 |
| resolved_current_team_verified | 4 |

## Named Rows

| Player | Pos | Selected team | Repair status | Quarantine | Data needed |
| --- | --- | --- | --- | --- | --- |
| Stefon Diggs | WR | - | current_status_verified_no_team | 1 | Local RotoWire source verifies no current NFL team; do not invent a team. |
| Joe Mixon | RB | - | current_status_verified_no_team | 1 | Local RotoWire source verifies no current NFL team; do not invent a team. |
| Keenan Allen | WR | - | current_status_verified_no_team | 1 | Local RotoWire source verifies no current NFL team; do not invent a team. |
| Jauan Jennings | WR | MIN | resolved_current_team_verified | 0 | No current-team repair needed from available local sources. |
| Kareem Hunt | RB | - | current_status_verified_no_team | 1 | Local RotoWire source verifies no current NFL team; do not invent a team. |
| Gabe Davis | WR | - | current_status_verified_no_team | 1 | Local RotoWire source verifies no current NFL team; do not invent a team. |
| Zach Ertz | TE | - | current_status_verified_no_team | 1 | Local RotoWire source verifies no current NFL team; do not invent a team. |
| David Njoku | TE | LAC | resolved_current_team_verified | 0 | No current-team repair needed from available local sources. |
| Najee Harris | RB | - | current_status_verified_no_team | 1 | Local RotoWire source verifies no current NFL team; do not invent a team. |
| Nick Chubb | RB | - | current_status_verified_no_team | 1 | Local RotoWire source verifies no current NFL team; do not invent a team. |
| Darren Waller | TE | - | current_status_verified_no_team | 1 | Local RotoWire source verifies no current NFL team; do not invent a team. |
| Aaron Rodgers | QB | PIT | resolved_current_team_verified | 0 | No current-team repair needed from available local sources. |
| Matt Prater | K | - | intentionally_hidden_kicker | 1 | Kicker hidden by default; current-team repair is not required for default QB/RB/WR/TE Rankings review. |
| Darius Slayton | WR | NYG | resolved_current_team_verified | 0 | No current-team repair needed from available local sources. |

## Interpretation

Rows with `unresolved_missing_current_team_source` remain capped/quarantined until a local current NFL team/status source is imported or repaired. Historical stats, old checkpoints, fantasy roster/team names, and component context were not allowed to clear the current-team source gap.
