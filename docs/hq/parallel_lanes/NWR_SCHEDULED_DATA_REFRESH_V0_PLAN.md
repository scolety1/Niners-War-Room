# NWR Scheduled Data Refresh V0 Plan

## Purpose

NWR needs repeatable local source refreshes without asking Tim to manually move data between lanes. Scheduled Data Refresh V0 defines a local-only pull, snapshot, normalize, audit, and approval flow for league state, optional stats/vendor context, and annual college football refreshes.

This plan does not create hosted CI/CD, deploy anything, run simulations, or approve any source for final draft-day use. Scheduled jobs may create raw snapshots, reports, and validated `latest_candidate` Lane Exchange packages. They must never automatically create or overwrite `latest_approved` or `pinned_live_snapshot`.

## Architecture

Official local roots:

```text
C:\NWR_SHARED_DATA\lane_exchange\
C:\NWR_SHARED_DATA\lane_exchange_registry\lane_exchange_v0_registry.json
C:\NWR_SHARED_DATA\scheduled_ingest\
C:\NWR_SHARED_DATA\scheduled_ingest\logs\
C:\NWR_SHARED_DATA\scheduled_ingest\reports\
```

Layer 1 pullers:

- `sleeper_pull.py` or equivalent: public Sleeper league-state pulls.
- `vendor_stats_pull.py` or equivalent: selected vendor/stat source pulls, disabled until vendor approval.
- `college_data_pull.py` or equivalent: annual college football source refresh, disabled until draft date/source contract is known.

Layer 2 raw snapshots:

Each pull writes timestamped local-only source folders:

```text
C:\NWR_SHARED_DATA\scheduled_ingest\<source>\<YYYYMMDD_HHMMSS>\
```

Each raw snapshot should include:

- source name
- endpoint list
- retrieval timestamp
- source identifiers
- row counts
- SHA256
- status
- warning/error notes
- redacted config summary
- no secrets

Layer 3 normalizers:

Normalizers convert safe source data into `latest_candidate` Lane Exchange packages only when fields, row counts, hashes, and identity constraints validate.

Layer 4 audit gate:

QA/Data Hygiene should eventually become the gatekeeper, but it remains HOLD until a safe repo/worktree exists. Until then, Master may create read-only audit reports. Scheduled jobs must stop at raw snapshot, report, or `latest_candidate`.

Layer 5 approval:

- `latest_candidate`: allowed from scheduled/producer jobs after validation.
- `latest_approved`: explicit Tim/Master/QA approval only.
- `pinned_live_snapshot`: explicit final live-test or draft-day approval only.

## Source Schedule

| Source | Frequency | Default Time | Status | Purpose | Output Ceiling |
| --- | --- | --- | --- | --- | --- |
| Sleeper API | Monday / Wednesday / Friday | local morning | Ready to design | league state, rosters, draft order, traded picks, transactions, dropped-player evidence, roster/user/team mappings | raw snapshots, reports, validated `latest_candidate` |
| Stats/vendor | every 2 days | local morning | HOLD | optional display-only stats/projections/injuries/news after vendor verification | raw snapshots and reports first; candidates later |
| College football | once yearly, about two weeks before fantasy rookie draft | configurable | HOLD until draft date known | rookie/offseason source refresh | raw snapshot and Rookie-approved handoff candidate only |

Recommended local times:

- Sleeper: 7:30 AM local time on Monday, Wednesday, Friday.
- Stats/vendor: 8:00 AM local time every two days, only after source approval.
- College football: 9:00 AM local time on the configured annual refresh date.

## Data Flow

1. Puller reads local-only config/secrets.
2. Puller calls source endpoints read-only.
3. Puller writes timestamped raw snapshot under `scheduled_ingest`.
4. Puller writes a small status report under `scheduled_ingest\reports`.
5. Normalizer validates source schema, row counts, SHA256, identity joins, duplicate keys, and forbidden fields.
6. If valid and allowed, normalizer writes a timestamped `latest_candidate` Lane Exchange package.
7. Audit report records GREEN/YELLOW/RED status.
8. Master/QA/Tim reviews candidate.
9. Separate explicit approval may update `latest_approved`.

Scheduled jobs must never overwrite last known approved data.

## Sleeper Packages

Possible raw snapshots:

- league details
- users
- rosters
- drafts
- draft details
- draft picks when available
- traded picks
- transactions

Possible Lane Exchange candidates:

- `sleeper_state/league_rosters_snapshot`
- `sleeper_state/draft_pick_ownership_snapshot`
- `sleeper_state/traded_picks_snapshot`
- `sleeper_state/transactions_snapshot`
- `league_state/pick_order`, only if source-backed and validated
- `league_state/nwr_picks`, only if source-backed and validated

Sleeper is source of truth for league-state ownership questions, including pick ownership conflicts. It may provide dropped-player evidence through completed transactions and current roster state, but official dropped-veteran approval remains Tim/Master gated.

Do not infer official dropped players from incomplete rosters unless marked as proposed evidence requiring Tim/Master approval.

## Stats/Vendor Packages

RotoWire is currently YELLOW:

- no API key is available
- license and NFL entitlement are unverified
- fields and player identity mapping are unverified
- package surface appears projection/news/injury oriented, not historical-stat oriented

Possible future packages after approval:

- `rotowire_context/projections_injuries_display_context`
- `market_behavior/display_only_market_context`
- `stats_context/player_stats_display_context`, only if a true historical stats source is later chosen

Vendor stats/projections/news/injuries must remain display-only context unless Tim/Master explicitly approves a separate source policy.

Vendor data must not enter:

- `model_value/veteran_private_values`
- private value formulas
- hidden ranking or sort logic
- ADP/market/private-value blends
- production probabilities, bands, or promoted artifacts
- final draft-day decisions

## College Football Packages

College football refreshes should run once yearly, roughly two weeks before the fantasy rookie draft.

Possible packages:

- `college_context/rookie_source_refresh`
- `rookie_hq/source_refresh_candidate`, only if Rookie HQ later approves the handoff format

College refreshes must not:

- run constantly
- auto-change Rookie HQ formulas
- auto-change Rookie rankings/order
- auto-promote Rookie board artifacts
- bypass Rookie HQ guardrails

## Lane Exchange Rules

- Scheduled jobs may create `latest_candidate`.
- Scheduled jobs must not create or update `latest_approved`.
- Scheduled jobs must not create or update `pinned_live_snapshot`.
- Every package must include a manifest with source, branch/head or source identifier, row count, SHA256, created timestamp, approval status, allowed uses, forbidden uses, and data classification flags.
- Every candidate must preserve no-private-value, no-market/ADP, and display-only flags where applicable.
- Bad validation must not update `latest_candidate` unless Tim/Master explicitly approves a separate failure-candidate workflow.

## Security And Secrets

Secrets must stay outside Git.

Preferred secret locations:

- local environment variables
- Windows Credential Manager
- local-only config under `C:\NWR_SHARED_DATA\secrets\`

Forbidden:

- `.env` inside any Git repo
- printing full keys
- committing keys
- committing raw licensed vendor data unless license explicitly allows it
- storing raw vendor payloads in Master docs

Reports should include only redacted config summaries, such as:

```text
ROTOWIRE_API_KEY=present length=32
```

Never print or store the full value.

## Failure Behavior

Failures create logs and reports only.

Hard failures:

- missing required IDs
- missing API key
- API auth failure
- schema changes
- row-count anomalies
- duplicate pick IDs
- unresolved player identity
- forbidden private/market/ADP fields in non-market packages
- source path outside allowed local roots

Failure status:

- RED: cannot trust source output; do not update candidate.
- YELLOW: source output exists but requires human review; do not promote.
- GREEN: source output and candidate validation pass; candidate may be reviewed for approval.

Staleness warnings:

- Sleeper league state older than 72 hours during draft week should be YELLOW.
- Sleeper league state older than 24 hours on draft day should be RED for live use.
- Vendor context older than 48 hours should be YELLOW if used for display.
- College football source older than the configured annual refresh window should be YELLOW for Rookie refresh planning.

## Draft Windows Task Scheduler Examples

Do not create these tasks yet. These are proposed commands only.

Sleeper, Monday / Wednesday / Friday:

```powershell
$action = New-ScheduledTaskAction `
  -Execute "powershell.exe" `
  -Argument "-NoProfile -ExecutionPolicy Bypass -File C:\NWR_SHARED_DATA\scheduled_ingest\scripts\run_sleeper_pull.ps1"

$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Wednesday,Friday -At 7:30am

$settings = New-ScheduledTaskSettingsSet `
  -StartWhenAvailable `
  -RestartCount 2 `
  -RestartInterval (New-TimeSpan -Minutes 15) `
  -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

Register-ScheduledTask `
  -TaskName "NWR Sleeper Scheduled Pull V0" `
  -Action $action `
  -Trigger $trigger `
  -Settings $settings `
  -Description "Local-only NWR Sleeper source snapshot pull. Does not approve Lane Exchange data."
```

Stats/vendor, every 2 days after approval:

```powershell
$trigger = New-ScheduledTaskTrigger -Daily -DaysInterval 2 -At 8:00am
```

College football, once yearly:

```powershell
# Replace <YYYY-MM-DD> after Tim provides the fantasy rookie draft date.
$trigger = New-ScheduledTaskTrigger -Once -At "<YYYY-MM-DD>T09:00:00"
```

Recommended scheduler settings:

- Run only when the user is logged in for V0.
- Do not wake the computer by default.
- Retry up to 2 times with a 15-minute interval.
- Write logs to `C:\NWR_SHARED_DATA\scheduled_ingest\logs\`.
- Write status reports to `C:\NWR_SHARED_DATA\scheduled_ingest\reports\`.
- Keep raw snapshots local-only.
- Do not run if another scheduled ingest is already active.

Wake-from-sleep can be enabled later if Tim wants unattended draft-week freshness.

## Local Scaffold

V0 local-only folders:

```text
C:\NWR_SHARED_DATA\scheduled_ingest\
C:\NWR_SHARED_DATA\scheduled_ingest\logs\
C:\NWR_SHARED_DATA\scheduled_ingest\reports\
C:\NWR_SHARED_DATA\scheduled_ingest\sleeper\
C:\NWR_SHARED_DATA\scheduled_ingest\vendor_stats\
C:\NWR_SHARED_DATA\scheduled_ingest\college_football\
```

No scheduled tasks are created by this plan.

## Open Questions For Tim

- Confirm Sleeper `league_id`.
- Confirm Sleeper `draft_id`, or allow puller to use the current league `draft_id`.
- Confirm exact fantasy rookie draft date.
- Choose stats/vendor source.
- Confirm whether a RotoWire API key exists.
- Confirm whether the RotoWire license covers local NWR use and NFL endpoints.
- Choose preferred run times.
- Decide whether scheduled jobs may run when the machine is locked.
- Decide whether scheduled jobs may wake the computer.
- Decide whether pulls should update `latest_candidate` automatically or only write raw snapshots first.
- Decide who approves scheduled candidates while QA/Data Hygiene remains HOLD.

## Recommended Next Implementation Prompts

1. Master: create local-only scheduled ingest skeleton scripts under `C:\NWR_SHARED_DATA\scheduled_ingest\scripts\`, with no secrets and no scheduled tasks.
2. Master: implement `sleeper_pull.py` to write raw snapshots and reports only.
3. Master: implement Sleeper normalizer dry run for `league_state/pick_order` and `league_state/nwr_picks`, writing candidates only after validation.
4. Mock Draft: add read-only support for staleness warnings from Lane Exchange manifests.
5. Master: run RotoWire Phase 2 vendor spike only after Tim provides a licensed key outside Git.
6. Rookie HQ: define approved annual college football refresh handoff format before any scheduled college pull writes Rookie candidates.

## Verdict

GREEN for Scheduled Data Refresh V0 design and local-only folder scaffold.

YELLOW for implementation because no puller scripts or scheduled tasks are approved yet, vendor source remains unchosen, RotoWire remains unverified, and college refresh timing depends on Tim's rookie draft date.
