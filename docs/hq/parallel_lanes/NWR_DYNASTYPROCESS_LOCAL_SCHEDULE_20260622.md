# NWR DynastyProcess Local Schedule - 2026-06-22

## Task

- Task name: `NWR DynastyProcess Market Baseline Refresh`
- Normal refresh: Friday `06:00` local machine time
- Backup retry / stale check: Saturday `08:00` local machine time

DynastyProcess upstream runs `weekly-playervalues` at cron `23 2 * * 5`, which is Friday `02:23 UTC` and Thursday evening in Mountain daylight time. NWR waits until Friday morning local time so the upstream workflow has hours to complete. The Saturday run catches stale, unchanged, or failed Friday refreshes before draft or trade work.

## Register

Run from the repo root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\register_dynastyprocess_refresh_task.ps1
```

The task runs as the current Windows user and does not require secrets. If Windows policy blocks registration, run the command above manually in an interactive PowerShell session and review the error.

## Unregister

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\unregister_dynastyprocess_refresh_task.ps1
```

Unregistering removes only the scheduled task. It does not delete cache, logs, or derived docs artifacts.

## Manual Run

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_dynastyprocess_refresh_task.ps1
```

The wrapper changes to:

```text
C:\NWR\Niners-War-Room
```

Then runs:

```powershell
.\.venv\Scripts\python.exe scripts\refresh_dynastyprocess_market_baseline_v1.py
```

## Logs

Logs are written outside the repo:

```text
C:\NWR_SHARED_DATA\market_sources\dynastyprocess\logs\
```

Each run writes timestamped stdout and stderr logs. These logs are raw local operational artifacts and must not be committed.

## Freshness Report

Latest freshness report:

```text
docs\hq\parallel_lanes\dynastyprocess_market_baseline_20260622\dp_freshness_report.csv
```

Key fields:

- `freshness_status`
- `upstream_scrape_date`
- `upstream_latest_commit_sha`
- `upstream_latest_commit_timestamp`
- `local_cache_path`
- `market_baseline_stale_warning`

## Freshness Statuses

- `GREEN_CURRENT`: current weekly scrape and newer than prior local snapshot.
- `GREEN_SAME_WEEK_NO_CHANGE`: current week but upstream values are unchanged.
- `YELLOW_STALE`: scrape date older than 8 days or upstream commit older than expected.
- `RED_STALE`: scrape date older than 14 days.
- `YELLOW_FETCH_FAILED_USING_LAST_CACHE`: upstream fetch failed but a usable cache exists.
- `RED_NO_VALID_CACHE`: fetch failed and no usable cache exists.

Yellow or red context must be shown as stale market baseline if exposed later. DynastyProcess remains display-only market context and must not drive NWR rank/model/app logic.

## Before Draft Or Trade Sessions

1. Run the manual wrapper.
2. Confirm `freshness_status` in `dp_freshness_report.csv`.
3. If status is yellow or red, retry once and review upstream DynastyProcess status.
4. If still stale, keep the data display-only with a visible stale warning.
5. Do not update source truth, final board rank, latest_candidate, latest_approved, pinned snapshots, or model/rank logic.
