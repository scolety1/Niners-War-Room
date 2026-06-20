# NWR Sleeper Scheduled Puller V0

Date: 2026-06-20

Owner: Master/Main HQ

## Purpose

Sleeper Scheduled Puller V0 creates local-only raw Sleeper API snapshots and redacted reports for NWR Scheduled Data Refresh V0.

Sleeper is the first implementation target because it is the source of league truth for:

- league settings
- users and team mappings
- rosters
- draft list
- traded picks
- draft details
- draft picks
- transaction evidence when specific transaction rounds are requested

This puller does not create Lane Exchange packages, does not update `latest_candidate`, does not update `latest_approved`, does not approve final draft-day data, does not run simulations, and does not deploy.

## Known League Configuration

| Field | Value |
| --- | --- |
| League | `Las Vegas Enginerds` |
| Season | `2026` |
| Sleeper league ID | `1344772855908290560` |
| Sleeper draft ID | `1353280212753723392` |

The IDs are CLI defaults for convenience, not secrets. They can be overridden with command arguments.

## Script

```text
scripts/sleeper_scheduled_pull_v0.py
```

Default local-only output root:

```text
C:\NWR_SHARED_DATA\scheduled_ingest\sleeper\
```

Each run writes a timestamped snapshot folder:

```text
C:\NWR_SHARED_DATA\scheduled_ingest\sleeper\<YYYYMMDD_HHMMSS>\
```

Each snapshot includes raw JSON endpoint files, `snapshot_metadata.json`, and `sleeper_pull_report.md`.

## Endpoints

Required endpoints:

| File | Sleeper path |
| --- | --- |
| `league.json` | `league/<league_id>` |
| `users.json` | `league/<league_id>/users` |
| `rosters.json` | `league/<league_id>/rosters` |
| `drafts.json` | `league/<league_id>/drafts` |
| `traded_picks.json` | `league/<league_id>/traded_picks` |
| `draft_details.json` | `draft/<draft_id>` |
| `draft_picks.json` | `draft/<draft_id>/picks` |

Optional endpoints:

| File | Sleeper path |
| --- | --- |
| `transactions_round_<n>.json` | `league/<league_id>/transactions/<n>` |

Transaction rounds are intentionally explicit. Pass `--transaction-rounds 1,2,3` only when Master/Tim wants those rounds captured. If no rounds are passed, transactions are skipped and the report records a warning.

## Example Local Run

```powershell
$python = "C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $python scripts/sleeper_scheduled_pull_v0.py `
  --league-id 1344772855908290560 `
  --draft-id 1353280212753723392 `
  --season 2026 `
  --league-name "Las Vegas Enginerds" `
  --output-root C:\NWR_SHARED_DATA\scheduled_ingest\sleeper
```

Optional transaction pull:

```powershell
& $python scripts/sleeper_scheduled_pull_v0.py --transaction-rounds 1,2,3
```

Do not create Windows scheduled tasks yet. This script is the local puller scaffold only.

## Report Contents

The redacted report includes:

- endpoint status
- row counts
- byte counts
- SHA256 hashes
- warnings
- explicit guardrails

It does not print or commit raw API payloads.

## Guardrails

- Raw Sleeper API responses stay outside Git.
- `C:\NWR_SHARED_DATA` must not be committed.
- No Lane Exchange package is created.
- `latest_candidate` is not updated.
- `latest_approved` is not updated.
- No final draft-day approval is granted.
- No simulation, recommendation, deployment, production app wiring, private value, hidden sort, probability, band, or promoted artifact path is approved.

## Validation

Tests use fake responses and temporary directories only:

```powershell
pytest tests/test_sleeper_scheduled_pull_v0.py
ruff check scripts/sleeper_scheduled_pull_v0.py tests/test_sleeper_scheduled_pull_v0.py
```

## Next Step

After this scaffold is accepted, the next prompt should create a local-only normalizer design for Sleeper-derived candidate packages, still without publishing Lane Exchange packages:

```text
Design Sleeper candidate normalizers for league_state/pick_order, league_state/nwr_picks, sleeper_state/league_rosters_snapshot, sleeper_state/traded_picks_snapshot, and sleeper_state/transactions_snapshot. Do not create packages yet. Use the raw snapshot metadata and fake fixtures to define schemas, validation, stale-data checks, and forbidden-use rules.
```

## Master Verdict

GREEN for local-only Sleeper raw snapshot/report scaffolding.

YELLOW for automation because no Windows scheduled task, Lane Exchange candidate publishing, or approval promotion is created by V0.
