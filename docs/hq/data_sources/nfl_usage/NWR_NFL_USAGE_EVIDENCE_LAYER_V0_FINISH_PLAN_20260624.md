# NFL Usage Evidence Layer V0 Finish Plan

## Current Checkpoint

- Branch: `work/hq-parallel-control`
- Starting HEAD: `b6554d22d6ac68c771c315d457e123ce3e7ac916`
- Starting status: clean and aligned with origin
- V0 infrastructure already completed: source contract, docs, review artifacts, fail-closed services, validation/quarantine harness, schema fingerprint service, focused tests, and closeout docs

## Remaining Blockers

- `nflreadpy` was not installed in the repo `.venv`.
- Live field-only smoke was not run.
- Exact live field inventory and schema fingerprints were pending.
- Review artifacts still showed YELLOW dry-run placeholders.
- Optional read-only review page remained gated off.

## Dependency Plan

Use the repo's explicit dependency files:
- `pyproject.toml`
- `requirements.txt`

Add only `nflreadpy`. Do not install globally. Do not vendor package code. Install into `.venv` only.

## Live Smoke Plan

Use `C:\NWR_SHARED_DATA\nfl_usage_cache\` for any raw/cache material. Attempt smallest safe field smokes for:
- player_stats
- snap_counts
- pbp
- nextgen_stats
- participation
- ftn_charting
- pfr_advstats
- rosters/player IDs/crosswalks

Commit only row counts, column names, schema fingerprints, validation summaries, and reports.

## Field Inventory Plan

For each successful or skipped loader, record:
- source family
- loader name
- observed columns
- observed dtypes
- allow/block status
- source attribution
- schema fingerprint
- quarantine status
- `model_input_allowed=no`
- `app_wiring_allowed=no`

## Review Artifact Regeneration Plan

Regenerate the small CSVs under `docs/hq/data_sources/nfl_usage/review_artifacts/` from live summaries. Large normalized data, if any, stays under shared cache and remains untracked.

## Optional Review Page Criteria

Only add `/nfl-usage-evidence-review` if live validation is GREEN, all repo-safe artifacts load, no raw data is tracked, and the page reads only committed summary CSVs.

## Stop Conditions

- dependency manager unclear
- package install fails
- source download too large/unreliable
- live schema cannot be safely sampled
- raw data appears in Git
- unexpected app/model/rank/source-truth diffs appear

## Validation Checklist

- focused pytest
- Ruff on touched Python
- Python compile
- CSV load validation
- `git diff --check`
- no raw/shared/local_exports/runtime files tracked
- no app/model/rank/source-truth diffs except an explicitly gated read-only page
- frozen board remains 66 rows
- pinned hash unchanged
- latest_candidate/latest_approved untouched

## Commit/Push Policy

Commit and push only when the lane is GREEN or safely YELLOW with blockers documented and no guardrail violations.
