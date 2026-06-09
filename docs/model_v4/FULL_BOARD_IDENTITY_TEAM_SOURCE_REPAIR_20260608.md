# Full Board Identity Team Source Repair - 2026-06-08

This source cleanup defines Rankings identity/team precedence and classifies team warnings. It does not tune formulas, change scores, mutate generated active rankings, or touch the Decision Board.

## Canonical Source Precedence

- Identity join key priority: `player_id` for source joins, then normalized `player_name + position` for Model v4 row joins.
- Display name priority: movement-audit name when preserving old-vs-new audit context, then full-board `player_name`, then active pack name.
- Current NFL team/status priority: normalized local `rotowire_nfl_team_status` exact match, then `fact_rosters.nfl_team`, then `fact_official_rankings.nfl_team`, then `dim_players.nfl_team`, then `current_player_value_full_board.nfl_team` as a derived fallback.
- RotoWire `FA`/teamless rows verify no current team but cannot invent a team.
- Historical/context teams: old 80-row checkpoint teams and imported component source teams are context only; they cannot override current-team sources.
- Active-board team handling: `model_outputs.csv` has no NFL team field, so active-board current team is read from roster/official/dim sidecars.
- Model v4 source team handling: full-board current-value team is derived from the active truth set and is not allowed to override conflicting current source files.
- Injury/status team handling: no injury/status team file is present in the active pack; missing source stays blank.
- Rookie/prospect team handling: rookie board does not provide current NFL team authority for active veteran Rankings rows.
- True mismatch means two current-team sources conflict. Historical-only mismatch means current sources agree but old/context team differs.
- Historical-only rows can rank with a visible context warning. Current-source conflicts, missing current team, missing canonical id, or missing disclosure stay quarantined.

## Repair Summary

| Metric | Count |
| --- | ---: |
| audit_rows | 61 |
| resolved_current_team_verified | 7 |
| resolved_historical_team_only | 44 |
| unresolved_current_source_conflict | 0 |
| unresolved_missing_current_team_source | 1 |
| current_status_verified_no_team | 9 |
| rows_should_remain_quarantined | 1 |
| historical_only_downgraded | 44 |
