# Merge Safety Report

## Scope

- Branch: `work/rookie-depth-chart-nondrafted-watchlist-v1-20260630`
- Base HEAD: `9c8038dfa17e7a22bbb06adc12cf92bd1026ff8a`
- Output directory: `docs/hq/rookie_model/rookie_depth_chart_nondrafted_watchlist_v1_20260630/`

## Merge Order

The UDFA pilot `6ef9ca9e2747a97359e576cb14cc834bae8a9419` and high-production non-drafted watchlist `0d4a9fe5db3ca3d7fdf1ea187dd86626a6d4a923` were not merged into the base control branch when this parallel lane was created. Merge predecessor review packets first if ordered Rookie Data Hygiene history is required.

## Guardrail Confirmations

- No original entry-status artifact changed in place.
- No app files changed.
- No Rankings, Draft Room, Gate F/G, or model-output behavior changed.
- No pinned snapshots changed.
- No `latest_candidate` or `latest_approved` changed.
- No source-truth behavior changed.
- No protected/raw/private paths are intended to be tracked.
- No secrets are intended to be tracked.

## Commands And Summarized Output

- `git rev-parse origin/work/hq-parallel-control`
  - `9c8038dfa17e7a22bbb06adc12cf92bd1026ff8a`
- Merge-order checks before branch creation
  - `UDFA_PILOT_MERGED=no`
  - `HIGH_PROD_WATCHLIST_MERGED=no`
- CSV integrity check over source and output CSVs
  - `CSV_INTEGRITY_OK`
  - `ENTRY_COUNTS_OK drafted=1999 likely_udfa_needs_review=2514 confirmed_udfa=0`
  - `DEPTH_TEMPLATE_ROWS=0`
  - `WATCHLIST_CANDIDATES=0`
  - `IDENTITY_BLOCKERS=0`
  - `IGNORE_SUMMARY_TOTAL=2514`
  - `MISSING_DEPTH_CHART_DATA_UNKNOWN_OK`
  - `NO_FAKE_ROUND_8_OR_ZERO_DRAFT_CAPITAL_OK`
- `git diff --name-only -- docs\hq\rookie_model\rookie_entry_status_hygiene_v1_20260630 docs\hq\rookie_model\rookie_entry_status_hygiene_qa_v1_20260630 templates\real_data_inputs\nflverse_stats_upgrade templates\real_data_inputs\data_pack docs\model_v4\ROTOWIRE_DEPTH_CHART_MAY22_SNAPSHOT.md`
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
