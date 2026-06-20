# NWR Operator Status V0

Date: 2026-06-20

Owner: Master/Main HQ

## Purpose

NWR Operator Status V0 is a read-only Master status script for local NWR automation and Lane Exchange state.

It summarizes:

- latest Sleeper raw snapshot and report
- latest nflverse raw snapshot and report
- Lane Exchange `latest_candidate` packages
- Lane Exchange `latest_approved` packages
- required Mock Draft package readiness
- `stats_context` candidate readiness
- stale or missing package warnings
- candidates newer than approvals
- first-local-live-test-only approvals
- blocked systems and next safe action

It does not create or update Lane Exchange packages, `latest_candidate`, `latest_approved`, scheduled tasks, simulations, deployments, private value, hidden ranking/sorting, or lane worktree files.

## Script

```text
scripts/nwr_operator_status_v0.py
```

Default shared-data root:

```text
C:\NWR_SHARED_DATA\
```

Default local-only report root:

```text
C:\NWR_SHARED_DATA\scheduled_ingest\reports\operator_status\
```

## Usage

Print concise terminal summary only:

```powershell
$python = "C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $python scripts/nwr_operator_status_v0.py
```

Print summary and write a local-only report:

```powershell
& $python scripts/nwr_operator_status_v0.py --write-report
```

The report is local-only and must not be committed.

## Inspected Paths

The script reads:

```text
C:\NWR_SHARED_DATA\lane_exchange\
C:\NWR_SHARED_DATA\lane_exchange_registry\lane_exchange_v0_registry.json
C:\NWR_SHARED_DATA\scheduled_ingest\sleeper\
C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\
C:\NWR_SHARED_DATA\scheduled_ingest\reports\
C:\NWR_SHARED_DATA\live_test_reports\
```

Missing paths produce YELLOW warnings instead of crashes.

## Package Checks

Required Mock Draft approved packages:

- `rookie_hq/frozen_rookie_mock_input`
- `drop_decision/dropped_veterans`
- `drop_decision/unavailable_players`
- `league_state/pick_order`
- `league_state/nwr_picks`
- `model_value/veteran_private_values`

Expected `stats_context` candidates:

- `stats_context/player_weekly_stats_display_context`
- `stats_context/player_season_stats_display_context`
- `stats_context/player_usage_context`
- `stats_context/player_stats_crosscheck_report`

The script reports packages where:

- `latest_candidate` exists
- `latest_approved` exists
- candidate timestamp appears newer than approved timestamp
- approval text indicates first local live-test validation only
- manifest paths are missing or unreadable

## Blocked Systems

Operator Status V0 always surfaces these blocks:

- QA/Data Hygiene HOLD
- final draft-day approval
- simulations/recommendations
- hosted deployment

## Guardrails

- Read-only by default.
- Reports are written only with `--write-report`.
- No Lane Exchange packages are created.
- `latest_candidate` is not updated.
- `latest_approved` is not updated.
- No simulations, recommendations, deployments, hosted runtime, scheduled tasks, private value, hidden ranks/sorts, or model behavior are created.
- No other lane worktrees are touched.
- `C:\NWR_SHARED_DATA` contents must not be committed.
- Raw data, secrets, `.env`, `data`, `local_exports`, caches, and generated artifacts must not be committed.

## Validation

Tests use fake temp directories and fake manifests only:

```powershell
pytest tests/test_nwr_operator_status_v0.py
ruff check scripts/nwr_operator_status_v0.py tests/test_nwr_operator_status_v0.py
```

Test coverage includes:

- missing paths produce warnings, not crashes
- newer candidate than approved is flagged
- first-local-live-test-only approval is surfaced
- no report is written unless explicitly requested
- `latest_approved` files are not mutated
- required Mock Draft and `stats_context` package status tables render

## Master Verdict

GREEN for read-only operator status scaffold.

YELLOW for actual operational readiness whenever warnings or blocked systems remain, because promotions, simulations, final draft-day approval, QA/Data Hygiene, and deployment are all separate gates.
