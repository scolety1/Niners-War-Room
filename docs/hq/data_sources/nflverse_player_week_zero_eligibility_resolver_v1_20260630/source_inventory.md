# Source Inventory

Verdict: `YELLOW_ZERO_ELIGIBILITY_PARTIAL_WITH_REMAINING_SOURCE_GAPS`

## Approved/Tracked Sources Found

- NFLVerse player_stats weekly admitted receipt: `docs/hq/data_sources/nflverse_player_stats_row_level_source_admission_v1_20260630/player_stats_row_level_receipt.csv`
- Local admitted player_stats weekly source: `C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\player_stats_source_admission_v1_20260630\player_stats_weekly.csv` read-only, SHA matched `a38c47ea830e6929e8de31d822496862d13873d13689ff90d2e50dac854901ba`
- Observed-row full scoring sidecar: `docs/hq/outcomes/nflverse_observed_row_full_scoring_sidecar_builder_v1_20260630/observed_row_full_scoring_sidecar_artifact.csv`
- Full scoring parity rerun packet: `docs/hq/outcomes/nflverse_full_scoring_parity_rerun_v1_20260630/`
- Outcome row-level labels: `docs/hq/outcomes/outcome_row_level_label_source_admission_v1_20260630/`
- Player context display artifact: `docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv`
- Availability denominator artifact: `docs/hq/data_sources/nflverse_availability_denominator_display_v1_20260630/availability_denominator_display_artifact.csv`
- Dataset registry/policy: `docs/hq/data_sources/nflverse_dataset_level_refresh_health_20260630/`
- Approved local final snapshot: `C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\player_context_display_final_20260630` read-only for weekly_rosters, rosters, schedules, injuries, snap_counts, players, ff_playerids, teams

## Sources Missing Or Not Sufficient

- No approved direct return touchdown field was found in the admitted player_stats schema.
- `special_teams_tds` exists but was not used as a substitute for return touchdowns.
- Weekly roster active status alone was not treated as in-game participation; snap-count evidence was required for missing player_stats safe-zero rows.
- Identity-gated current player rows remain gated.
