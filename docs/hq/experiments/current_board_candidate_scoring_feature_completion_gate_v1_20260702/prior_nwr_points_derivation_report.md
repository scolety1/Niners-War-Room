# prior_nwr_points Derivation Report

Status: `COMPLETED_FOR_EXACT_2025_REG_OBSERVED_ROWS`

Derivation:

1. Read local-only NFLVerse `player_stats_weekly` snapshot.
2. Verify SHA256 `a38c47ea830e6929e8de31d822496862d13873d13689ff90d2e50dac854901ba` against the Core Usage Review receipt.
3. Keep only completed `2025` REG rows.
4. Drop exact duplicate rows.
5. Require every NWR scoring component column to be non-null in observed rows.
6. Score each observed player-week with `config/nwr_scoring_rules_nwr_1qb_nonppr_fd_v1.json`.
7. Sum scored player-week rows by GSIS player id.

Blocked inputs:

- Imported `fantasy_points` and `fantasy_points_ppr`.
- Market, ADP, vendor projections, ranks, current context, routes, TPRR, YPRR, red-zone sidecars, and ambiguous `rz_att`.

No absent player was assigned zero points.
