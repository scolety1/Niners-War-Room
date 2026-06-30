# Merge Safety Report

## Scope

- Branch: `work/rookie-udfa-source-policy-confirmation-pilot-v1-20260630`
- Output directory: `docs/hq/rookie_model/rookie_udfa_source_policy_confirmation_pilot_v1_20260630/`
- Input entry-status artifact was read only.

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
  - `caaae3a606f6d6f7c955d63ed02eafdb508a7692`
- Required input artifact presence check
  - Entry-status hygiene packet present.
  - QA addendum present.
  - Drafted-only Outcome review packet present.
- CSV integrity check over input and output CSVs
  - `CSV_INTEGRITY_OK`
  - `LIKELY_UDFA_REVIEWED=2514`
  - `CONFIRMED_UDFA_CANDIDATES=0`
  - `BLOCKED_ROWS=2514`
  - `RECOMMENDED_STATUS_COUNTS likely_udfa_needs_review=2460 name_collision=54`
  - `PATCH_PROPOSAL_ROWS=0`
  - `FLAGS_LOCKED review_only=true model_use_allowed=false training_allowed=false`
  - `NO_FAKE_ROUND_8_OR_ZERO_DRAFT_CAPITAL_OK`
- `git diff --name-only -- docs\hq\rookie_model\rookie_entry_status_hygiene_v1_20260630 docs\hq\rookie_model\rookie_entry_status_hygiene_qa_v1_20260630 docs\hq\rookie_model\rookie_outcome_drafted_only_review_v1_20260630`
  - No output; original entry-status, QA, and drafted-only Outcome packet inputs were not changed.
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
