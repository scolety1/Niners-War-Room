# NFL Usage Live Smoke Report

## Verdict

GREEN. `nflreadpy` live field-only smoke ran for 2024 source samples and committed only sanitized summary artifacts.

## Cache

- Cache root: `C:\NWR_SHARED_DATA\nfl_usage_cache\nflreadpy_cache`
- Raw/cache committed: no
- Repo committed artifacts: columns, row counts, schema fingerprints, validation summaries, and quarantine summaries only

## Sources Attempted

- player_stats
- snap_counts
- pbp
- nextgen_stats passing
- nextgen_stats receiving
- nextgen_stats rushing
- participation
- ftn_charting
- pfr_advstats pass
- pfr_advstats rush
- pfr_advstats rec
- rosters
- players
- ff_playerids

All attempted sources returned live schemas and row counts.

## Field Quarantine

The smoke observed raw-source fields that are not accepted evidence, including fantasy point fields and score-state fields. They are field-level quarantined in the live inventory and validation reports. They are not accepted as model features, app fields, rankings inputs, or source truth.

## Artifacts

- `review_artifacts/live_smoke/nfl_usage_live_smoke_summary_v0.csv`
- `review_artifacts/live_field_inventory/nfl_usage_live_field_inventory_v0.csv`
- `review_artifacts/live_field_inventory/nfl_usage_live_schema_fingerprints_v0.csv`
- `review_artifacts/live_field_inventory/nfl_usage_live_field_gap_report_v0.csv`
- `review_artifacts/validation/nfl_usage_live_validation_report_v0.csv`
- `review_artifacts/validation/nfl_usage_live_quarantine_report_v0.csv`
