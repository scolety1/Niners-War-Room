# NWR DynastyProcess Refresh Schedule - 2026-06-22

## Verdict

GREEN. DynastyProcess refresh policy is now explicit and the connector writes freshness metadata into every derived market-context artifact.

## Upstream Schedule

- Upstream repository: https://github.com/dynastyprocess/data
- Upstream workflow: `weekly-playervalues`
- Workflow file: `.github/workflows/weekly-playervalues.yml`
- Cron: `23 2 * * 5`
- UTC time: Friday `02:23 UTC`
- Denver daylight time conversion: Thursday night about `20:23 MDT`

The workflow can also run by `workflow_dispatch`, but NWR should assume the weekly cron is the normal cadence.

## NWR Pull Time

Recommended normal pull:

```text
Friday 06:00 America/Denver
```

That gives the upstream Friday 02:23 UTC workflow several hours to finish and publish `files/values.csv`, `files/values-players.csv`, `files/values-picks.csv`, `files/db_playerids.csv`, and `files/db_fpecr_latest.csv`.

Backup retry:

```text
Saturday morning America/Denver
```

Use the backup retry when Friday morning sees stale scrape dates, unchanged upstream files, failed fetches, or GitHub/API instability.

## Manual Pre-Draft Refresh

Run from the repo root:

```powershell
.\.venv\Scripts\python.exe scripts\refresh_dynastyprocess_market_baseline_v1.py
```

Optional explicit label:

```powershell
.\.venv\Scripts\python.exe scripts\refresh_dynastyprocess_market_baseline_v1.py --snapshot-label 20260626_dynastyprocess_weekly
```

The command writes raw upstream files to:

```text
C:\NWR_SHARED_DATA\market_sources\dynastyprocess\<snapshot_label>
```

It writes repo-safe derived artifacts to:

```text
docs/hq/parallel_lanes/dynastyprocess_market_baseline_20260622/
```

## Freshness Metadata

Every refresh stores:

- `nwr_fetch_timestamp`
- `upstream_scrape_date`
- `upstream_latest_commit_sha`
- `upstream_latest_commit_timestamp`
- `upstream_workflow_name`
- `upstream_expected_cron`
- `local_cache_path`
- `derived_artifact_path`
- `freshness_status`
- `market_baseline_stale_warning`

The single-row freshness report is:

```text
docs/hq/parallel_lanes/dynastyprocess_market_baseline_20260622/dp_freshness_report.csv
```

Current report from the 2026-06-23 cache:

- Freshness status: `GREEN_CURRENT`
- Upstream scrape date: `2026-06-19`
- Upstream commit: `a38911c0080e5623741eaa3bfcd63d1db98a5342`
- Upstream commit timestamp: `2026-06-19T07:33:57Z`
- NWR fetch timestamp: `2026-06-23T22:37:05+00:00`

## Freshness Thresholds

| Status | Meaning | Action |
| --- | --- | --- |
| `GREEN_CURRENT` | Scrape date is inside expected weekly window and newer than prior local snapshot. | Safe for display-only review. |
| `GREEN_SAME_WEEK_NO_CHANGE` | Scrape date is current week but values are unchanged from prior local snapshot. | Safe for display-only review; note no upstream change. |
| `YELLOW_STALE` | Scrape date is older than 8 days or upstream commit is older than expected. | Show "Market baseline stale"; retry Saturday or manually investigate. |
| `RED_STALE` | Scrape date is older than 14 days. | Do not treat as current; use only with prominent stale warning. |
| `YELLOW_FETCH_FAILED_USING_LAST_CACHE` | Upstream fetch failed but a valid local cache exists. | Derived artifacts can be created, but must show stale/fallback warning. |
| `RED_NO_VALID_CACHE` | Fetch failed and no valid cache exists. | No usable market baseline; command exits nonzero. |

## If Friday Pull Is Stale

1. Confirm `dp_freshness_report.csv`.
2. Check whether upstream `weekly-playervalues` completed.
3. Retry Saturday morning Mountain time.
4. If still stale, keep derived artifacts only as display-only stale context.
5. Do not wire stale DynastyProcess values into model/rank logic.
6. Do not update source truth, final board rank, latest_candidate, latest_approved, or pinned snapshots.

## Policy Reminder

DynastyProcess remains a display-only market baseline, player ID crosswalk, age-source candidate, and pick-value sanity layer. It must not drive NWR model scoring, candidate rank, hidden sort, recommendations, simulations, or final draft decisions without later Master approval.
