# Merge Safety Report

## Scope

- Branch: `work/rookie-entry-status-hygiene-v1-20260630`
- Base HEAD: `18ecf909103439aad4077aafd798107bebe7bc64`
- Artifact directory: `docs/hq/rookie_model/rookie_entry_status_hygiene_v1_20260630/`

## Guardrail Confirmations

- No app files changed.
- No Rankings, Draft Room, Gate F/G, or model outputs changed.
- No pinned snapshots changed.
- No `latest_candidate` or `latest_approved` changed.
- No production refresh behavior changed.
- No protected/raw/private paths are intended to be tracked.
- No secrets are intended to be tracked.

## Commands And Summarized Output

- `git rev-parse HEAD`
  - `18ecf909103439aad4077aafd798107bebe7bc64`
- `git branch --contains 9803f7994b57273b652de004648526e315b6ad5a`
  - Confirmed the prior review-only packet commit is contained in the base branch history.
- `git status --short --branch`
  - Only the review-only rookie entry-status hygiene artifact directory was untracked before staging.
- `python -m pytest tests\test_rookie_historical_label_source_policy_v1_20260630.py tests\test_rookie_draft_class_gsis_bridge_v1_20260630.py tests\test_rookie_draft_capital_bg_gates_20260629.py tests\test_rookie_outcome_rd_guardrails.py tests\test_rookie_outcome_columns_gated_guardrails.py tests\test_cfbd_rookie_approval_and_bg_gates_20260629.py tests\test_cfbd_review_artifacts_v1.py tests\test_nwr_outcome_scoring_service.py tests\test_nwr_outcome_training_row_service.py`
  - `62 passed in 0.45s`
- `git diff --check`
  - Passed with no whitespace errors.
- Changed-Python Ruff check
  - `RUFF_SKIPPED_NO_CHANGED_PYTHON`
- Changed-Python compile check
  - `PY_COMPILE_SKIPPED_NO_CHANGED_PYTHON`
- Forbidden tracked path scan over changed paths
  - `FORBIDDEN_TRACKED_PATH_SCAN_OK`
- Protected artifact/source path scan over changed paths
  - `PROTECTED_ARTIFACT_SOURCE_PATH_SCAN_OK`
- Entry-status CSV integrity scan
  - `ENTRY_STATUS_ALLOWED_OK`
  - `NON_DRAFT_ZERO_FIELDS_OK`
  - `FAKE_ROUND_8_OK`
  - Entry-status counts: `drafted=1999`, `confirmed_udfa=0`, `likely_udfa_needs_review=2514`, `free_agent_rookie_needs_review=0`, `wrong_universe=138`, `name_collision=2`, `unknown=0`.
