# Player Stats Row-Level Source Admission Summary

Verdict: `GREEN_PLAYER_STATS_ROW_LEVEL_SOURCE_ADMITTED_REVIEW_ONLY`

## Decision

A safe review-only row-level NFLVerse `player_stats` source receipt is admitted for future sidecar builder use. The source rows were generated through the approved local-only NFLVerse safe runner, not copied into git.

## Runner Result

- Runner: `scripts\run_nflverse_refresh_v0.ps1`
- Puller: `scripts\nflverse_scheduled_pull_v0.py`
- Snapshot label: `player_stats_source_admission_v1_20260630`
- Snapshot root: `C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\player_stats_source_admission_v1_20260630`
- Seasons requested: `2024-2025`
- `player_stats_weekly` rows: 76804
- `player_stats_weekly` columns: 231
- `player_stats_weekly` SHA-256: `a38c47ea830e6929e8de31d822496862d13873d13689ff90d2e50dac854901ba`
- `player_stats_seasonal` rows: 42419
- `player_stats_seasonal` columns: 229
- `player_stats_seasonal` SHA-256: `57f76cfeee3211885f6d05504cc61b6529d023d5eb15a60ae21cc81c21c07b59`

## Admission Boundary

The tracked receipt admits the source only for review-only sidecar substrate building. It does not admit player_stats as label truth, model input, training input, source truth, rank logic, hidden sort, recommendations, trade value, or pick value.

Quarantined fields from the runner remain excluded from review use until a later source-policy lane explicitly approves them.
