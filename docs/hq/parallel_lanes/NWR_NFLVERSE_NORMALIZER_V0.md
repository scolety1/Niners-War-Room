# NWR nflverse Normalizer V0

Date: 2026-06-20

Owner: Master/Main HQ

## Purpose

nflverse Normalizer V0 converts local-only nflverse raw snapshots into display-only `stats_context` Lane Exchange `latest_candidate` packages.

It does not create `latest_approved`, does not overwrite existing approved packages, does not create private value, does not modify `veteran_private_values`, does not create hidden rank/sort/model behavior, does not run simulations, and does not deploy.

## Script

```text
scripts/nflverse_normalize_snapshot_v0.py
```

Default Lane Exchange output root:

```text
C:\NWR_SHARED_DATA\lane_exchange\
```

Candidate writes are disabled by default. The script performs dry-run/report mode unless `--write-candidates` is passed.

## Supported Candidate Packages

| Package | Source files | Status |
| --- | --- | --- |
| `stats_context/player_weekly_stats_display_context` | `weekly_stats.csv` | Supported when present |
| `stats_context/player_season_stats_display_context` | `season_stats.csv` | Optional; skipped with YELLOW warning if missing |
| `stats_context/player_usage_context` | `snap_counts.csv`, `participation.csv`, `opportunity.csv` | Supported from whichever files are present |
| `stats_context/player_stats_crosscheck_report` | snapshot metadata and dataset summaries | Always produced for source audit |

## Allowed Display Fields

V0 permits only boring display/stat context fields:

- player IDs and names
- team
- position
- season
- week
- opponent
- passing attempts, completions, yards, TD, INT
- rushing attempts/carries, yards, TD
- targets, receptions, receiving yards, receiving TD
- first downs
- snap counts and snap percentages
- routes or participation fields only as display/usage context when clearly labeled

Every candidate row is marked:

```text
approval_status=candidate
allowed_use=display_stat_context_only
```

## Quarantine Policy

These fields are excluded from display candidate CSVs and retained only in local raw snapshots:

- `fantasy_points`
- `fantasy_points_ppr`
- EPA
- CPOE
- PACR/RACR
- WOPR
- expected/diff fields
- share fields
- ranks/rankings
- scores
- values
- ADP
- market fields
- tiers
- sort keys
- probabilities
- projections
- anything that looks like model scoring or private value

Quarantined fields are recorded in the normalizer report and candidate manifests, but they are not copied into display candidate data.

## Manifest Policy

Every candidate manifest includes:

- `approval_status: candidate`
- `contains_private_value: false`
- `contains_market_data: false`
- `contains_adp: false`
- `allowed_use` limited to display/stat context and review
- `forbidden_use` including private value, hidden sort/rank, draft recommendation, final draft decision, model training, simulation, deployment, and `latest_approved`
- source snapshot path
- row count
- SHA256
- source dataset list
- quarantine summary

`latest_approved.json` is never created or updated.

## Usage

Dry-run/report only:

```powershell
$python = "C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $python scripts/nflverse_normalize_snapshot_v0.py `
  --snapshot-dir C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\20260620_212500_live_limited_committed
```

Explicit candidate write:

```powershell
& $python scripts/nflverse_normalize_snapshot_v0.py `
  --snapshot-dir C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\20260620_212500_live_limited_committed `
  --write-candidates
```

The explicit write command creates timestamped package folders and `latest_candidate.json` pointers only. It never writes `latest_approved.json`.

## Current Live Snapshot Fit

The current live limited snapshot has:

```text
C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\20260620_212500_live_limited_committed\
```

Loaded datasets:

- `rosters`: 6,353 rows
- `weekly_stats`: 38,402 rows
- `snap_counts`: 53,227 rows

Because `season_stats.csv` is not present in that snapshot, V0 should produce:

- weekly display candidate
- usage display candidate
- crosscheck report candidate

and should skip the season display candidate with a YELLOW warning.

## Guardrails

- Raw stats outputs stay local-only outside Git.
- `C:\NWR_SHARED_DATA` must not be committed.
- No raw nflverse data is committed.
- No Lane Exchange package is written unless `--write-candidates` is explicitly used.
- `latest_candidate` may be written only for display/stat context review.
- `latest_approved` is never created or updated.
- Stats are not NWR private value.
- Stats are not `veteran_private_values`.
- Stats must not be blended with ADP, market fields, private value, model fields, recommendations, hidden ranks, or hidden sorts.
- No model training, simulation, deployment, production app wiring, or final draft-day use is approved.

## Validation

Tests use fake snapshot fixtures and temporary directories only:

```powershell
pytest tests/test_nflverse_normalize_snapshot_v0.py
ruff check scripts/nflverse_normalize_snapshot_v0.py tests/test_nflverse_normalize_snapshot_v0.py
```

Test coverage includes:

- dry-run mode writes no candidates
- candidate mode writes manifests and `latest_candidate` only
- no `latest_approved` creation
- quarantined fields excluded from display candidate data
- no private/market/ADP flags
- row count and SHA validation
- missing optional `season_stats.csv` handled as YELLOW, not a crash

## Next Step

After this normalizer is accepted, Master may run a dry-run against the live limited snapshot and review the report. Candidate generation against the live snapshot should remain a separate explicit approval.

Recommended next prompt:

```text
Run nflverse Normalizer V0 dry-run against C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\20260620_212500_live_limited_committed\. Do not write candidates. Report package counts, quarantine summary, and whether it is safe to create display-only latest_candidate packages in a follow-up.
```

## Master Verdict

GREEN for display-only nflverse normalizer scaffold.

YELLOW for downstream use until live dry-run and candidate audit are reviewed.
