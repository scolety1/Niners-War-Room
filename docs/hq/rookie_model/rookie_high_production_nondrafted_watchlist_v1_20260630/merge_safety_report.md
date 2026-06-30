# Merge Safety Report

## Scope

- Branch: `work/rookie-high-production-nondrafted-watchlist-v1-20260630`
- Base/parent commit: `6ef9ca9e2747a97359e576cb14cc834bae8a9419`
- Parent packet: `docs/hq/rookie_model/rookie_udfa_source_policy_confirmation_pilot_v1_20260630/`
- Output directory: `docs/hq/rookie_model/rookie_high_production_nondrafted_watchlist_v1_20260630/`

## Merge Order

The UDFA pilot commit `6ef9ca9e2747a97359e576cb14cc834bae8a9419` must merge into `work/hq-parallel-control` before this watchlist branch is merged.

## Guardrail Confirmations

- This branch is based on the UDFA pilot commit.
- No original entry-status artifact changed in place.
- No app files changed.
- No Rankings, Draft Room, Gate F/G, or model-output behavior changed.
- No pinned snapshots changed.
- No `latest_candidate` or `latest_approved` changed.
- No source-truth behavior changed.
- No protected/raw/private paths are intended to be tracked.
- No secrets are intended to be tracked.

## Commands And Summarized Output

- `git rev-parse HEAD`
  - `6ef9ca9e2747a97359e576cb14cc834bae8a9419`
- Parent artifact presence check
  - `docs/hq/rookie_model/rookie_udfa_source_policy_confirmation_pilot_v1_20260630/` present.
- CSV integrity check over input and output CSVs
  - `CSV_INTEGRITY_OK`
  - `PARENT_LIKELY_ROWS=2514`
  - `APPROVED_PRODUCTION_CONTEXT_AVAILABLE=no`
  - `CFBD_ROWS=16938 review_only=16938 identity_review_required=16938 approved_historical_candidates=0`
  - `WATCHLIST_CANDIDATES=0`
  - `IDENTITY_RISK_BLOCKERS=0`
  - `IGNORE_SUMMARY_TOTAL=2514`
  - `NO_FAKE_ROUND_8_OR_ZERO_DRAFT_CAPITAL_OK`
- `git diff --name-only -- docs\hq\rookie_model\rookie_entry_status_hygiene_v1_20260630 docs\hq\rookie_model\rookie_udfa_source_policy_confirmation_pilot_v1_20260630 docs\hq\data_sources\cfbd_review_artifacts_20260624 docs\hq\rookie_model\rookie_model_historical_cfbd_and_outcome_backfill_policy_20260630`
  - No output; source input artifacts were not changed.
- `git diff --check`
  - Passed with no whitespace errors.
- Focused pytest
  - Skipped; this lane changes only review-only Markdown/CSV artifacts and touches no tests or production Python.
- Changed-Python Ruff check
  - Skipped; no changed Python is being committed.
- Changed-Python compile check
  - Skipped; no changed Python is being committed.
- `git diff --cached --check`
  - Passed with no whitespace errors after staging.
- Forbidden tracked path scan over staged paths
  - `FORBIDDEN_TRACKED_PATH_SCAN_OK`
- Protected artifact/source path scan over staged paths
  - `PROTECTED_ARTIFACT_SOURCE_PATH_SCAN_OK`
