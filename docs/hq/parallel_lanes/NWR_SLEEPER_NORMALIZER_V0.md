# NWR Sleeper Normalizer V0

Date: 2026-06-20

Owner: Master/Main HQ

## Purpose

Sleeper Normalizer V0 converts a local-only Sleeper raw snapshot into validated dry-run reports and, only when explicitly requested, Lane Exchange `latest_candidate` packages.

It reads raw snapshots produced by `scripts/sleeper_scheduled_pull_v0.py`, including the first live local snapshot:

```text
C:\NWR_SHARED_DATA\scheduled_ingest\sleeper\20260620_200109\
```

This normalizer does not create `latest_approved`, does not overwrite existing approved packages, does not infer final draft-day truth, does not run simulations, and does not deploy.

## Script

```text
scripts/sleeper_normalize_snapshot_v0.py
```

Default Lane Exchange output root:

```text
C:\NWR_SHARED_DATA\lane_exchange\
```

Candidate writes are disabled by default. The script performs dry-run/report mode unless `--write-candidates` is passed.

## Supported Candidate Packages

| Package | Source | Purpose |
| --- | --- | --- |
| `sleeper_state/league_rosters_snapshot` | `rosters.json` + `users.json` | Roster and team ownership source audit |
| `sleeper_state/draft_pick_ownership_snapshot` | `draft_details.json` + `traded_picks.json` | Sleeper-backed pick ownership reconstruction |
| `sleeper_state/traded_picks_snapshot` | `traded_picks.json` | Traded-pick evidence |
| `sleeper_state/transactions_snapshot` | `transactions_round_*.json` | Transaction evidence review |
| `league_state/pick_order` | normalized pick ownership | Mock Draft pick-order candidate |
| `league_state/nwr_picks` | normalized pick ownership + NWR roster match | Mock Draft NWR-picks candidate |

## Pre-Draft Pick Logic

When `draft_picks.json` is empty, V0 reconstructs the draft from:

- `draft_details.draft_order`
- `league rosters` owner-to-roster mapping
- `traded_picks`

The current NWR draft expectation is:

```text
5 rounds x 10 teams = 50 picks
```

The normalizer validates:

- 50 pick rows
- unique `overall_pick`
- unique `pick_label`
- one mapped draft slot per team
- current pick ownership from Sleeper traded-pick data

If `draft_picks.json` contains completed picks, V0 fails closed. Completed-draft or in-draft normalization should be a later explicit V1 behavior.

## NWR Picks

By default, V0 identifies the NWR roster by matching team name/display name to:

```text
Niners
```

An explicit override is available:

```powershell
--nwr-roster-id 7
```

If NWR cannot be matched, `league_state/nwr_picks` is empty and the report records a warning.

## Usage

Dry-run/report only:

```powershell
$python = "C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $python scripts/sleeper_normalize_snapshot_v0.py `
  --snapshot-dir C:\NWR_SHARED_DATA\scheduled_ingest\sleeper\20260620_200109
```

Explicit candidate write:

```powershell
& $python scripts/sleeper_normalize_snapshot_v0.py `
  --snapshot-dir C:\NWR_SHARED_DATA\scheduled_ingest\sleeper\20260620_200109 `
  --write-candidates
```

The explicit write command creates timestamped package folders and `latest_candidate.json` pointers only. It never writes `latest_approved.json`.

## Manifest Policy

Every candidate manifest includes:

- `source_lane`
- `source_repo`
- `source_branch`
- `source_head`
- `package_name`
- `schema_version`
- `data_file`
- `row_count`
- `sha256`
- `created_at`
- `approval_status: candidate`
- `approved_for`
- `allowed_use`
- `forbidden_use`
- `contains_private_value`
- `contains_market_data`
- `contains_adp`
- source warnings and notes

## Guardrails

- Raw Sleeper API data stays outside Git.
- `C:\NWR_SHARED_DATA` must not be committed.
- Candidate writes require `--write-candidates`.
- `latest_approved` is never created or updated.
- Existing approved packages are never overwritten.
- Candidates are not final draft-day truth.
- No simulations, recommendations, deployment, app wiring, private value, hidden sort, probabilities, bands, or promoted artifacts are approved.

## Validation

Tests use fake snapshots and temporary directories only:

```powershell
pytest tests/test_sleeper_normalize_snapshot_v0.py
ruff check scripts/sleeper_normalize_snapshot_v0.py tests/test_sleeper_normalize_snapshot_v0.py
```

Test coverage includes:

- pre-draft reconstruction from `draft_order` plus `traded_picks`
- duplicate pick detection
- dry-run mode does not write candidates
- candidate mode writes manifests and `latest_candidate` only
- `latest_approved` is not created

## Next Step

After this normalizer is accepted, Master may explicitly run candidate generation against the live local snapshot and then run a read-only candidate audit. Approval to `latest_approved` remains a separate Tim/Master gate.

Recommended next prompt:

```text
Run Sleeper Normalizer V0 against the live local snapshot with --write-candidates, then audit the six created latest_candidate packages. Do not create latest_approved. Do not run simulations or deploy. Report row counts, hashes, warnings, and whether pick_order/nwr_picks align with the current approved Mock Draft local-live-test state.
```

## Master Verdict

GREEN for local-only Sleeper normalization scaffold.

YELLOW for downstream use until candidates are explicitly generated, audited, and separately approved.
