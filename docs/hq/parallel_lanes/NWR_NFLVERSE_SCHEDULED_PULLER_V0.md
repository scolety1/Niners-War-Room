# NWR nflverse Scheduled Puller V0

Date: 2026-06-20

Owner: Master/Main HQ

## Purpose

nflverse Scheduled Puller V0 creates local-only raw stats snapshots and redacted reports from `nflreadpy`.

It supports NWR's Stats Source V0 decision: nflverse/nflreadpy is the primary free historical/player stats source candidate. Stats remain display/stat context only until a later source policy approves any stronger use.

This puller does not create Lane Exchange packages, does not update `latest_candidate`, does not update `latest_approved`, does not create scheduled tasks, does not run simulations, and does not deploy.

## Script

```text
scripts/nflverse_scheduled_pull_v0.py
```

Default local-only output root:

```text
C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\
```

Snapshot folder shape:

```text
C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\<YYYYMMDD_HHMMSS>\
```

The folder may contain local raw CSV outputs, `snapshot_metadata.json`, and `nflverse_pull_report.md`. None of these files should be committed.

## Dependency Policy

The puller uses `nflreadpy` if it is available in the active Python environment.

If `nflreadpy` is unavailable, the puller fails closed with install guidance. It must not auto-install packages into any NWR Git repo.

Approved install location, when needed, is a local-only scratch/runtime outside repos.

## Supported Datasets

The V0 dataset names are:

| Dataset | Candidate nflreadpy functions | Purpose |
| --- | --- | --- |
| `weekly_stats` | `import_weekly_data`, `load_player_stats` | Weekly player production |
| `season_stats` | `import_seasonal_data`, `load_player_stats`, `load_seasonal_data` | Season-level player production |
| `rosters` | `import_rosters`, `load_rosters` | Player identity/team/position context |
| `weekly_rosters` | `import_weekly_rosters`, `load_rosters_weekly`, `load_weekly_rosters` | Week-specific roster identity context |
| `snap_counts` | `import_snap_counts`, `load_snap_counts` | Snap-count context |
| `participation` | `import_participation`, `load_participation` | Participation/routes-like context where supported |
| `opportunity` | `import_player_stats`, `load_ff_opportunity`, `load_opportunity`, `import_opportunity` | Opportunity/targets/carries/routes-like context where supported |

If a dataset function is not present in the installed `nflreadpy`, V0 marks that dataset `skipped` instead of inventing data.

## Usage

Dry scaffold/report without live imports:

```powershell
$python = "C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $python scripts/nflverse_scheduled_pull_v0.py `
  --seasons 2024 2025 `
  --skip-live
```

Live local pull, if `nflreadpy` is installed in the active local runtime:

```powershell
& $python scripts/nflverse_scheduled_pull_v0.py `
  --seasons 2024 2025
```

Subset pull:

```powershell
& $python scripts/nflverse_scheduled_pull_v0.py `
  --seasons 2025 `
  --datasets weekly_stats season_stats rosters
```

## Report Contents

The report and metadata include:

- package/tool/version
- seasons pulled
- datasets attempted
- dataset statuses
- row counts
- column counts
- field-name summaries
- likely player ID/name/team/season/week/position fields
- SHA256 values for local raw CSV outputs
- identity matching for the standard NWR sample player set
- structured identity matches with original query, source matched name, match type, and source field
- quarantined field warnings
- explicit guardrails

Reports do not include full raw data dumps.

## Field Policy

Raw local snapshots may contain fields that are not yet approved for NWR private value, hidden ranking, hidden sorting, model training, or draft decisions.

V0 flags these fields as quarantined:

- `fantasy_points`
- `fantasy_points_ppr`
- expected/diff fields
- EPA
- CPOE
- PACR/RACR
- WOPR
- target share, air-yard share, route share, snap share, and other share/advanced efficiency fields

Quarantined fields are not deleted from local raw snapshots, but they are blocked from private value or hidden decision logic unless a later source policy approves them.

## Sample Identity Set

The identity check searches loaded name fields for:

- Drake Maye
- Jaylen Warren
- Darren Waller
- Brock Purdy
- Dak Prescott
- Zay Flowers
- Keenan Allen
- Chris Olave
- Rashee Rice
- Jameson Williams
- Brian Thomas Jr
- Brian Thomas
- Alec Pierce

Identity matching is a source-audit check only. It does not create player aliases or repair any Lane Exchange package.

V0 includes one explicit sample-check alias:

```text
Brian Thomas <-> Brian Thomas Jr
```

This alias affects report matching only. It does not rewrite source data and does not create a Lane Exchange alias package.

The identity check searches common name fields including `player_name`, `player_display_name`, `full_name`, and `player`. The `player` field is needed for snap-count datasets.

## Guardrails

- Raw stats outputs stay local-only outside Git.
- `C:\NWR_SHARED_DATA` must not be committed.
- No Lane Exchange package is created.
- `latest_candidate` is not updated.
- `latest_approved` is not updated.
- Stats are display/stat context only.
- Stats are not NWR private value.
- Stats are not `veteran_private_values`.
- No hidden ranking, hidden sorting, model training, simulation, recommendation, deployment, production app wiring, or final draft-day use is approved.
- No `.env`, API key, secret, raw vendor data, or generated artifact is committed.

## Validation

Tests use fake `nflreadpy`-like loader responses and temporary directories only:

```powershell
pytest tests/test_nflverse_scheduled_pull_v0.py
ruff check scripts/nflverse_scheduled_pull_v0.py tests/test_nflverse_scheduled_pull_v0.py
```

Test coverage includes:

- metadata/report creation
- raw CSV output into temp directories
- SHA/row/column summaries
- quarantine-field detection
- Brian Thomas / Brian Thomas Jr alias identity reporting
- snap-count identity matching from the `player` field
- likely player ID/name/team/season/week/position field-role reporting
- missing `nflreadpy` fails safely
- skipped unsupported optional loader functions
- no Lane Exchange package or approval metadata is created

## Next Step

After this puller is accepted, Master may run it from a local-only runtime where `nflreadpy` is installed, then review the raw snapshot report.

Recommended next prompt:

```text
Run nflverse Scheduled Puller V0 from the approved local-only nflreadpy runtime for seasons 2024 2025. Do not create Lane Exchange packages. Do not update latest_candidate or latest_approved. Report dataset statuses, row counts, hashes, identity matches, quarantined fields, and whether weekly/season/usage context is sufficient for display-only stats candidate planning.
```

## Master Verdict

GREEN for local-only nflverse raw snapshot/report scaffolding.

YELLOW for downstream data use until a live pull is reviewed and a separate candidate-normalizer policy is approved.
