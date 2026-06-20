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

## Recommended API Source Hierarchy

| Priority | Source | Role | Schedule | Candidate Packages | V0 Decision |
| ---: | --- | --- | --- | --- | --- |
| 1 | Sleeper | League truth: league settings, rosters, users/team mappings, draft order, traded picks, transactions, ownership evidence | Monday / Wednesday / Friday local morning; optionally daily near draft week | `sleeper_state/league_rosters_snapshot`, `sleeper_state/draft_pick_ownership_snapshot`, `sleeper_state/traded_picks_snapshot`, `sleeper_state/transactions_snapshot`, `league_state/pick_order`, `league_state/nwr_picks` | GREEN to implement first |
| 2 | nflverse / nflfastR | NFL historical stats source candidate: historical production, player/team usage, play-by-play-derived stats | every 2-3 days if useful; weekly if mostly historical | `stats_context/player_stats_display_context`, `stats_context/player_usage_display_context`, future source-specific identity bridge packages | YELLOW pending stats spike |
| 3 | CollegeFootballData | College/rookie yearly refresh source candidate: college player/team/game data and rookie/offseason refresh | once yearly two weeks before rookie draft; optional post-NFL-Draft landing-spot refresh | `college_context/rookie_source_refresh`, `rookie_hq/source_refresh_candidate` only after Rookie HQ approves format | YELLOW pending API key/date/Rookie handoff |
| 4 | RotoWire | Optional paid display context only: injuries, news, weekly/daily projections | every 2 days only after key/license/field verification | `rotowire_context/projections_injuries_display_context` or `market_behavior/display_only_market_context` | YELLOW/HOLD |

Not recommended for V0:

- random scraping
- unverified GitHub clients as source of truth
- ESPN/Yahoo/FantasyPros integrations before Sleeper, nflverse, and CollegeFootballData are stable
- any source that cannot be licensed, cached, mapped to player identity, or audited safely

## Source Schedule

| Source | Frequency | Default Time | Status | Purpose | Output Ceiling |
| --- | --- | --- | --- | --- | --- |
| Sleeper API | Monday / Wednesday / Friday; optionally daily near draft week | local morning | Ready to implement first | league state, rosters, draft order, traded picks, transactions, dropped-player evidence, roster/user/team mappings | raw snapshots, reports, validated `latest_candidate` |
| nflverse / nflfastR | every 2-3 days if useful; weekly if mostly historical | local morning | HOLD pending stats spike | historical production, player/team usage, play-by-play-derived stat context | raw snapshots and display/stat-context candidates only |
| CollegeFootballData | once yearly, about two weeks before fantasy rookie draft; optional post-NFL-Draft refresh | configurable | HOLD until API key/date/Rookie format known | college/rookie source refresh | raw snapshot and Rookie-approved handoff candidate only |
| RotoWire | every 2 days only after approval | local morning | HOLD pending key/license/field verification | optional paid injuries/news/projections display context | raw snapshots and display-context candidates only |

Recommended local times:

- Sleeper: 7:30 AM local time on Monday, Wednesday, Friday.
- Sleeper draft-week option: 7:30 AM daily beginning when Tim/Master declares draft-week freshness mode.
- nflverse / nflfastR: 8:00 AM every 2-3 days if actively useful, or weekly if mostly historical.
- CollegeFootballData: 9:00 AM on the configured annual refresh date, plus optional post-NFL-Draft landing-spot refresh.
- RotoWire: 8:30 AM every two days only after source approval.

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

## nflverse / nflfastR Packages

nflverse / nflfastR is the preferred V0 candidate for true NFL historical stat context.

Possible source roles:

- historical player production
- player/team usage
- play-by-play-derived stats
- roster/team/player identity support where source licensing permits

Possible Lane Exchange candidates:

- `stats_context/player_stats_display_context`
- `stats_context/player_usage_display_context`
- `stats_context/nflverse_identity_bridge_candidate`

nflverse data starts as display/stat context only. It must not become private value, model-training input, hidden ranking/sort logic, probability/band input, or final draft-day decision authority unless Tim/Master later approves a separate source policy.

The stats spike must verify:

- source package/license terms
- update cadence
- player identifiers and join keys
- stable position/team fields
- row-count expectations
- whether source fields are historical facts or derived projections
- whether any source field represents market, ADP, editorial rank, probability, or hidden score

## RotoWire Packages

RotoWire is currently YELLOW:

- no API key is available
- license and NFL entitlement are unverified
- fields and player identity mapping are unverified
- package surface appears projection/news/injury oriented, not historical-stat oriented

Possible future packages after approval:

- `rotowire_context/projections_injuries_display_context`
- `market_behavior/display_only_market_context`

Vendor stats/projections/news/injuries must remain display-only context unless Tim/Master explicitly approves a separate source policy.

Vendor data must not enter:

- `model_value/veteran_private_values`
- private value formulas
- hidden ranking or sort logic
- ADP/market/private-value blends
- production probabilities, bands, or promoted artifacts
- final draft-day decisions
- model training

RotoWire is not the V0 historical stats source unless a later licensed endpoint proves actual historical stats, stable player identity, and acceptable local caching rights.

## College Football Packages

CollegeFootballData is the preferred V0 college/rookie source-refresh candidate. It requires an API key and should run once yearly, roughly two weeks before the fantasy rookie draft, with an optional post-NFL-Draft landing-spot refresh if Tim/Master approves.

Possible packages:

- `college_context/rookie_source_refresh`
- `rookie_hq/source_refresh_candidate`, only if Rookie HQ later approves the handoff format

CollegeFootballData refreshes must not:

- run constantly
- auto-change Rookie HQ formulas
- auto-change Rookie rankings/order
- auto-promote Rookie board artifacts
- bypass Rookie HQ guardrails

The CollegeFootballData spike must verify:

- API key location outside Git
- allowed local caching terms
- player identity fields
- school/team fields
- season/year coverage
- row-count expectations
- handoff format acceptable to Rookie HQ

## Lane Exchange Rules

- Scheduled jobs may create `latest_candidate`.
- Scheduled jobs must not create or update `latest_approved`.
- Scheduled jobs must not create or update `pinned_live_snapshot`.
- `latest_approved` requires explicit Tim/Master/QA approval after audit.
- `pinned_live_snapshot` requires explicit final live-test or draft-day approval.
- Every package must include a manifest with source, branch/head or source identifier, row count, SHA256, created timestamp, approval status, allowed uses, forbidden uses, and data classification flags.
- Every candidate must preserve no-private-value, no-market/ADP, and display-only flags where applicable.
- Bad validation must not update `latest_candidate` unless Tim/Master explicitly approves a separate failure-candidate workflow.

Candidates may be overwritten by later validated candidates only if the prior candidate remains preserved in its timestamped snapshot folder and reports clearly record the pointer update.

## Identity Mapping Requirements

Every scheduled candidate must identify its player/team/pick keys before it can be accepted downstream.

Minimum identity requirements:

- Sleeper: `league_id`, `draft_id` where applicable, `roster_id`, `owner_id`, display/team names, pick round/slot/overall labels, and transaction IDs where applicable.
- nflverse / nflfastR: stable player identifiers, player display name, position, NFL team, season/week, and explicit source field definitions.
- CollegeFootballData: stable player/school identifiers where available, player name, school/team, season, position where available, and source endpoint/date.
- RotoWire: stable RotoWire player ID if provided, player name, NFL team, position, feed date/week, and source endpoint.

Identity mismatch policy:

- exact ID match: GREEN if schema/row/hash checks pass.
- name/team/position-only match: YELLOW and human review required.
- ambiguous names, duplicate player IDs, duplicate pick IDs, or missing owner mappings: RED for candidate promotion.
- no scheduled job may silently resolve ambiguous names.

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
- using unlicensed vendor data in Lane Exchange candidates
- putting API keys in scheduled task command arguments

Reports should include only redacted config summaries, such as:

```text
ROTOWIRE_API_KEY=present length=32
```

Never print or store the full value.

Key expectations by source:

- Sleeper: public/read-only API; no key expected, but league/draft IDs must be explicit in reports.
- nflverse / nflfastR: verify package/source licenses before caching or publishing candidates.
- CollegeFootballData: API key required and must stay outside Git.
- RotoWire: API key and license confirmation required before endpoint calls.

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
- nflverse historical stat context older than one week should be YELLOW only if actively used for current display; historical archives may have a different freshness profile recorded in the manifest.
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

nflverse / nflfastR, weekly if mostly historical:

```powershell
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Tuesday -At 8:00am
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
- Confirm whether Sleeper should run daily during draft week.
- Confirm whether nflverse / nflfastR is approved as the first NFL stats spike source.
- Confirm whether CollegeFootballData API key exists and where it will be stored outside Git.
- Confirm whether post-NFL-Draft landing-spot refresh should be part of the annual college workflow.
- Confirm whether a RotoWire API key exists.
- Confirm whether the RotoWire license covers local NWR use and NFL endpoints.
- Confirm whether RotoWire is needed at all for draft week or can wait until after Sleeper/nflverse/CFBD stabilize.
- Choose preferred run times.
- Decide whether scheduled jobs may run when the machine is locked.
- Decide whether scheduled jobs may wake the computer.
- Decide whether pulls should update `latest_candidate` automatically or only write raw snapshots first.
- Decide who approves scheduled candidates while QA/Data Hygiene remains HOLD.

## Recommended Next Implementation Prompts

1. Master: implement the Sleeper scheduled puller to write raw snapshots and reports only.
2. Master: implement Sleeper candidate normalizers for `league_state/pick_order`, `league_state/nwr_picks`, rosters, and transactions, writing candidates only after validation.
3. Master: run an nflverse / nflfastR stats spike for historical production and usage display context.
4. Master and Rookie HQ: run a CollegeFootballData yearly rookie refresh spike after Tim provides the rookie draft date and API key location.
5. Master: run RotoWire Phase 2 only after Tim provides a licensed key and confirms NFL endpoint coverage/local use rights.
6. Mock Draft: add read-only support for staleness warnings from Lane Exchange manifests.

## Verdict

GREEN for Scheduled Data Refresh V0 design and local-only folder scaffold.

YELLOW for implementation because no puller scripts or scheduled tasks are approved yet, vendor source remains unchosen, RotoWire remains unverified, and college refresh timing depends on Tim's rookie draft date.
