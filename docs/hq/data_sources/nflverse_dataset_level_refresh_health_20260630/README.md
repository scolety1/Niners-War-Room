# NFLVerse Dataset-Level Refresh Health V1

Date: 2026-06-30

Status: GREEN implementation lane ready for review.

This lane splits nflverse Refresh/Data Health visibility from one coarse source row into
25 canonical dataset-level status rows. It is health/status/reporting only.

No model input, rank logic, source-truth, hidden-sort, `latest_candidate`, or
`latest_approved` behavior is changed.

## Canonical Dataset Rows

The persisted/reportable dataset IDs are the 25 packet IDs in
`nflverse_dataset_registry_v1.csv`. Legacy names such as `weekly_stats`,
`season_stats`, `pbp`, and `opportunity` are accepted only as loader aliases.

## Runtime Boundary

Raw/cache output remains local-only under `C:\NWR_SHARED_DATA\scheduled_ingest\nflverse`.
Tracked files in this lane are compact service code, tests, and docs/status summaries only.
