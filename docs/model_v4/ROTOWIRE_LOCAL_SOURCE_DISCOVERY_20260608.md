# RotoWire Local Source Discovery - 2026-06-08

This discovery used local files already present in the repo. It did not scrape RotoWire, call a live app, use credentials, or read browser/session data.

## Candidate Files Used

| Path | Type | Rows | Columns | Current team | Status | Injuries | Depth | Blocked value fields | Allowed use | Blocked use |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| local_exports\model_v4\workouts\latest\rotowire_workout_stats_may25.csv | csv | 2097 | `source|source_file|collected_at_utc|position|player|team|draft_year|event|height|height_inches|weight|arm|hand|forty|forty_pct|shuttle|shuttle_pct|cone|cone_pct|vertical|vertical_pct|broad|broad_pct|bench|bench_pct` | yes | yes_team_fa | no | no | no | current_team_status_display_identity_team_source_repair_injury_status_context_source_quarantine_resolution | do_not_use_for_nwr_dynasty_score_nwr_rank_tier_formula_weights_vorp_replacement_market_league_gaps_public_ranking_replacement_trade_cut_draft_recommendations_or_outcome_percentages |
| local_exports\model_v4\depth_charts\latest\rotowire_upcoming_depth_charts_may22.csv | csv | 727 | `source|source_file|collected_at_utc|team|position|depth_rank|slot|player|status|raw_player_cell` | yes | yes | yes | yes | no | current_team_status_display_identity_team_source_repair_injury_status_context_source_quarantine_resolution | do_not_use_for_nwr_dynasty_score_nwr_rank_tier_formula_weights_vorp_replacement_market_league_gaps_public_ranking_replacement_trade_cut_draft_recommendations_or_outcome_percentages |

## Discovery Conclusion

- `rotowire_workout_stats_may25.csv` has exact local player/team rows for the 12 unresolved non-kicker targets, including `FA` for teamless players.
- `rotowire_upcoming_depth_charts_may22.csv` provides current depth-chart team/status context for matched active players such as Jauan Jennings, David Njoku, Aaron Rodgers, and Darius Slayton.
- RotoWire projection, ranking, salary, ADP, market-like, and fantasy point fields are not normalized into the team/status source and remain blocked from private value.
