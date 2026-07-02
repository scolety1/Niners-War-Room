# Scoring Feature Decision

Decision: `PARTIAL_SCORING_FEATURES_COMPLETED_WITH_NULL_FENCES`

`prior_nwr_points`, `prior_games`, and `prior_nwr_ppg` can be safely generated for exact 2025 REG observed-row matches using:

- the checksum-matched local NFLVerse `player_stats_weekly` raw snapshot,
- existing NWR scoring rules,
- the merged full-scoring formula alignment packet,
- the prior candidate feature input gate's stable identity joins.

This decision does not approve candidate ranks, app wiring, live preview, production configs, hidden sort, recommendations, source-truth promotion, or formula promotion.

Rows without an exact 2025 REG observed-row scoring match remain null-fenced.
