# NWR NFLVerse Dataset-Level Intake + Refresh Health Implementation

Date: 2026-06-30

## Verdict

`GREEN_FEATURE_BRANCH_READY`

This lane replaces the old coarse `nflverse_public_data` refresh-health row with one
runner row plus dataset-level health rows. It is Refresh/Data Health visibility only.

## Implemented Rows

Runner row:

- `nflverse_refresh_runner`

Dataset rows:

- `nflverse_dataset_weekly_stats`
- `nflverse_dataset_season_stats`
- `nflverse_dataset_pbp`
- `nflverse_dataset_snap_counts`
- `nflverse_dataset_injuries`
- `nflverse_dataset_rosters`
- `nflverse_dataset_weekly_rosters`
- `nflverse_dataset_depth_charts`
- `nflverse_dataset_draft_picks`
- `nflverse_dataset_schedules`
- `nflverse_dataset_ff_playerids`
- `nflverse_dataset_participation`
- `nflverse_dataset_opportunity`

Configured in the existing Safe Refresh runner:

- `weekly_stats`
- `season_stats`
- `snap_counts`
- `rosters`
- `weekly_rosters`
- `participation`
- `opportunity`

Visible but `NOT_CONFIGURED` until a safe runner option is approved:

- `pbp`
- `injuries`
- `depth_charts`
- `draft_picks`
- `schedules`
- `ff_playerids`

## Health Checks

Each dataset row reports:

- row count
- column count
- schema fingerprint
- schema status
- coverage status
- freshness status
- missingness status
- source-policy status
- Safe Refresh health
- Full Safe Refresh health

Missing dataset evidence is reported as `Not enough information` or `NOT_CONFIGURED`.
It is never converted into zero, false, healthy, clean, no-role, no-injury, or
no-usage defaults.

## App Visibility

Updated surfaces:

- Refresh Data source registry and run results.
- Settings / Data Health loader results.
- Settings / Data Health refresh-health summary rows.

No Rankings, Outcome Lens, Live Draft, Mock Draft, model, source-truth, candidate, or
approval path was changed.

## Source Of Truth

Dataset health reads local-only snapshot metadata from:

- `C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\<snapshot>\snapshot_metadata.json`

It can also locate the latest snapshot from:

- `local_exports\refresh_data\nflverse\latest\nflverse_refresh_manifest.json`

Raw shared-data snapshots remain untracked.
