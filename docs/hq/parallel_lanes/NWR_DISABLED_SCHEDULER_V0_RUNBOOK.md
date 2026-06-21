# NWR Disabled Scheduler V0 Runbook

Date: 2026-06-20

Status: GREEN documentation and disabled-runner preparation only. No Windows scheduled tasks were created by this runbook.

## Purpose

Disabled Scheduler V0 prepares local runner scripts and operator instructions for NWR scheduled data refresh without enabling automation. The runners can pull local-only Sleeper and nflverse raw snapshots, optionally write `latest_candidate` packages, and produce read-only operator health reports. They never create or update `latest_approved`.

## Guardrails

- Do not create enabled scheduled tasks in V0.
- Do not auto-promote `latest_candidate` to `latest_approved`.
- Do not update `latest_approved` from any scheduled runner.
- Do not run simulations, generated pick paths, recommendations, deployments, or hosted jobs.
- Do not commit `C:\NWR_SHARED_DATA`, raw snapshots, reports, secrets, `.env`, `data`, `local_exports`, caches, dependency folders, or generated artifacts.
- Keep secrets outside Git. Sleeper uses public read-only endpoints. nflverse currently needs no key, but any future vendor key must stay outside repo paths.
- Scheduled pulls may create raw local snapshots and candidate reports only. Tim/Master/QA approval remains required for approvals and live/draft-day promotion.

## Local Runner Scripts

| Runner | Purpose | Writes | Approval behavior |
| --- | --- | --- | --- |
| `scripts/run_sleeper_refresh_v0.ps1` | Pull Sleeper league truth data and optionally run Sleeper normalizer in candidate mode | `C:\NWR_SHARED_DATA\scheduled_ingest\sleeper\`, `C:\NWR_SHARED_DATA\scheduled_ingest\logs\` | Never writes `latest_approved` |
| `scripts/run_nflverse_refresh_v0.ps1` | Pull nflverse display/stat context using local-only `nflreadpy` dependencies and optionally run normalizer in candidate mode | `C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\`, `C:\NWR_SHARED_DATA\scheduled_ingest\logs\` | Never writes `latest_approved` |
| `scripts/run_nwr_data_health_v0.ps1` | Run read-only operator status | `C:\NWR_SHARED_DATA\scheduled_ingest\reports\operator_status\`, `C:\NWR_SHARED_DATA\scheduled_ingest\logs\` | Read-only |

Candidate generation is opt-in through `-WriteCandidates`. Without that flag, refresh runners create raw snapshots and reports only.

The nflverse runner requests the expanded V1 display/stat dataset set by default: `weekly_stats`, `season_stats`, `rosters`, `weekly_rosters`, `snap_counts`, `participation`, and `opportunity`. Unsupported local-runtime datasets are soft-skipped with YELLOW warnings.

## Proposed Schedules

| Job | Proposed cadence | Local timing | Notes |
| --- | --- | --- | --- |
| Sleeper refresh | Monday / Wednesday / Friday | Local morning | May become daily during draft week after explicit approval |
| nflverse refresh | Every 2-3 days | Local morning | Display/stat context only; no private value use |
| NWR data health | After each pull or daily | Local morning | Read-only summary of snapshots, candidates, approvals, and blockers |

Recommended Task Scheduler settings when tasks are approved later:

- Run only when Tim is logged in for V0.
- Do not wake the computer until Tim explicitly approves that behavior.
- Retry once after a short delay on transient failure.
- Write runner transcripts to `C:\NWR_SHARED_DATA\scheduled_ingest\logs\`.
- Treat stale required league data as YELLOW/RED in operator status reports, not as automatic approval failure repair.

## Disabled Task Creation Examples

These commands are examples only. They create disabled tasks and should not be run until Tim/Master approves scheduler registration.

```powershell
$repo = "C:\NWR\Niners-War-Room"

$sleeperAction = New-ScheduledTaskAction `
  -Execute "powershell.exe" `
  -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$repo\scripts\run_sleeper_refresh_v0.ps1`""
$sleeperTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Wednesday,Friday -At 8:00am
Register-ScheduledTask `
  -TaskName "NWR Sleeper Refresh V0 DISABLED" `
  -Action $sleeperAction `
  -Trigger $sleeperTrigger `
  -Description "NWR Sleeper raw snapshot refresh. Disabled by default; no latest_approved automation." `
  -Disabled

$nflverseAction = New-ScheduledTaskAction `
  -Execute "powershell.exe" `
  -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$repo\scripts\run_nflverse_refresh_v0.ps1`""
$nflverseTrigger = New-ScheduledTaskTrigger -Daily -DaysInterval 2 -At 8:30am
Register-ScheduledTask `
  -TaskName "NWR nflverse Refresh V0 DISABLED" `
  -Action $nflverseAction `
  -Trigger $nflverseTrigger `
  -Description "NWR nflverse raw display/stat snapshot refresh. Disabled by default; no latest_approved automation." `
  -Disabled

$healthAction = New-ScheduledTaskAction `
  -Execute "powershell.exe" `
  -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$repo\scripts\run_nwr_data_health_v0.ps1`""
$healthTrigger = New-ScheduledTaskTrigger -Daily -At 9:00am
Register-ScheduledTask `
  -TaskName "NWR Data Health V0 DISABLED" `
  -Action $healthAction `
  -Trigger $healthTrigger `
  -Description "NWR read-only operator status report. Disabled by default." `
  -Disabled
```

## Enable Later

Only after Tim/Master approval:

```powershell
Enable-ScheduledTask -TaskName "NWR Sleeper Refresh V0 DISABLED"
Enable-ScheduledTask -TaskName "NWR nflverse Refresh V0 DISABLED"
Enable-ScheduledTask -TaskName "NWR Data Health V0 DISABLED"
```

If enabled, consider renaming tasks to remove `DISABLED` only after a separate approval pass.

## Manual Runner Examples

Raw Sleeper snapshot only:

```powershell
cd C:\NWR\Niners-War-Room
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_sleeper_refresh_v0.ps1
```

Sleeper raw snapshot plus `latest_candidate` generation:

```powershell
cd C:\NWR\Niners-War-Room
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_sleeper_refresh_v0.ps1 -WriteCandidates
```

nflverse raw display/stat snapshot only:

```powershell
cd C:\NWR\Niners-War-Room
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_nflverse_refresh_v0.ps1
```

nflverse raw snapshot plus display/stat `latest_candidate` generation:

```powershell
cd C:\NWR\Niners-War-Room
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_nflverse_refresh_v0.ps1 -WriteCandidates
```

Read-only operator health report:

```powershell
cd C:\NWR\Niners-War-Room
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_nwr_data_health_v0.ps1
```

## Logs and Reports

- Runner transcripts: `C:\NWR_SHARED_DATA\scheduled_ingest\logs\`
- Sleeper snapshots/reports: `C:\NWR_SHARED_DATA\scheduled_ingest\sleeper\`
- nflverse snapshots/reports: `C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\`
- Operator status reports: `C:\NWR_SHARED_DATA\scheduled_ingest\reports\operator_status\`

None of these local-only outputs are committed to Git.

## Stale Data Warnings

Operator Status V0 should surface stale or missing data warnings instead of attempting repair. The expected V0 interpretation is:

- GREEN: latest local snapshots and required approvals are present and aligned for the requested review scope.
- YELLOW: missing/stale candidate data, newer candidate than approval, first-local-live-test-only approvals, or optional package gaps.
- RED: missing required approved packages, schema/hash/row-count failures, unsafe package fields, or unresolved final draft-day gates.

## Troubleshooting

- If a runner fails before writing a snapshot, inspect the transcript under `scheduled_ingest\logs`.
- If Sleeper API calls fail, verify internet access and Sleeper IDs before rerunning.
- If nflverse fails to import `nflreadpy`, verify the local-only path `C:\NWR_SHARED_DATA\vendor_spikes\nflverse\scratch\pydeps\` exists and is passed through `PYTHONPATH`.
- If normalizer candidate generation fails, keep the previous candidate/approval untouched and review the generated report or transcript.
- If a task is accidentally enabled before approval, disable it immediately and record the incident before rerunning any refresh.

## Manual Approval Gates

- `latest_approved` packages require explicit Tim/Master/QA approval.
- `pinned_live_snapshot` requires explicit live-test or draft-day approval.
- Final draft-day use remains blocked until separate final gates pass.
- Stats/nflverse packages remain display/stat context only and are blocked from private value, hidden rank/sort, model training, draft recommendation, simulations, and final draft-day decisions unless a later source policy approves otherwise.

## Open Gates

- Tim/Master approval to register disabled tasks, if desired.
- Tim/Master approval to enable any task.
- Tim/Master/QA approval policy for scheduled `latest_candidate` generation frequency.
- QA/Data Hygiene remains HOLD until safely reactivated.
- Final draft-day approvals remain separate from scheduler readiness.
