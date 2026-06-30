# NFLVerse Schedule Future Coverage Audit

As-of date: `2026-06-30`
Schedule rows refreshed by approved runner: `272`
Schedule seasons: `2026`
Schedule weeks: `1-18`
Max game date before hardening packet: `2026-02-08`
Max game date after targeted 2026 schedules refresh: `2027-01-10`
Current/future rows as of 2026-06-30: `272`
Teams covered: `32`

The approved safe runner can refresh schedules without scraping or private data. This lane ran `scripts/run_nflverse_refresh_v0.ps1 -Seasons 2026 -Datasets schedules -SnapshotLabel player_context_hardening_schedule_20260630`.

The runner is not configured to pull 2026 by default; its default seasons are 2024 and 2025. A targeted safe refresh fixed the schedule blocker for display context, while keeping raw output under `C:\NWR_SHARED_DATA`.

Team aliases are not the main blocker. The artifact uses nflverse team codes for safe rows; `LAR` maps to `LA` and `JAC` maps to `JAX` when NWR team values are needed.

Allowed output remains team-level display context only: next game week/date, opponent, and bye week. No matchup strength, projected points, start/sit, win probability, rank/model input, hidden sort, trade value, or pick value is added.