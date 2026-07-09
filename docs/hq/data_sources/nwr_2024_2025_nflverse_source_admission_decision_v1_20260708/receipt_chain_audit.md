# Receipt-Chain Audit

This packet inspected only known local/tracked NWR nflverse evidence paths, not broad discovery.

Primary local snapshot path:

`C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\player_context_display_final_20260630\`

Tracked evidence packets:

- `docs/hq/data_sources/nflverse_core_usage_review_dataset_v1_20260701/`
- `docs/hq/data_sources/sleeper_nflverse_usage_redzone_source_admission_v1_20260701/`
- `docs/hq/data_sources/nflverse_lagged_usage_point_in_time_rules_v1_20260701/`
- `docs/hq/data_sources/nflverse_source_overlap_stat_availability_inventory_v1_20260701/`
- `docs/hq/data_sources/hq_advanced_metrics_source_backtest_v0_20260707/`

Detailed receipt rows are in `receipt_chain_audit_source_rows.csv`.

Every receipt row preserves `model_use_approved=false` and `source_truth_promoted=false` by policy. Raw/shared files remain untracked.
