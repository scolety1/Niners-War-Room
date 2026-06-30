# Merge Safety Report

## Scope

- Branch: `work/rookie-model-historical-cfbd-and-outcome-backfill-policy-20260630`
- Base HEAD: `ec0702ff467ef86a4973fc6e8e156fc7be89b49e`
- Artifact directory: `docs\hq\rookie_model\rookie_model_historical_cfbd_and_outcome_backfill_policy_20260630`

## Confirmations

- No app files changed.
- No Rankings, Draft Room, or model outputs changed.
- No pinned snapshots changed.
- No `latest_candidate` or `latest_approved` changed.
- No protected/raw/private paths are intended to be tracked.
- No secrets are intended to be tracked.
- No production refresh behavior changed.

## Commands And Summarized Output

| Command | Summarized output |
| --- | --- |
| `python -m pytest tests/test_rookie_historical_label_source_policy_v1_20260630.py tests/test_rookie_draft_class_gsis_bridge_v1_20260630.py tests/test_rookie_draft_capital_bg_gates_20260629.py tests/test_rookie_outcome_rd_guardrails.py tests/test_rookie_outcome_columns_gated_guardrails.py tests/test_cfbd_rookie_approval_and_bg_gates_20260629.py tests/test_cfbd_review_artifacts_v1.py tests/test_nwr_outcome_scoring_service.py tests/test_nwr_outcome_training_row_service.py` | PASS: 62 passed |
| `ruff check <changed python>` | SKIPPED: no changed Python files |
| `python -m py_compile <changed python>` | SKIPPED: no changed Python files |
| `git diff --check` | PASS |
| Forbidden tracked path scan over changed paths | PASS: no `C:\NWR_SHARED_DATA`, `C:\NWR_LOCAL_SECRETS`, `local_exports`, raw/cache/API/vendor/Gmail, runtime JSON, or secret paths changed |
| Protected artifact/source path scan over changed paths | PASS: no app files, Rankings/Draft Room/model outputs, final board/rank/tier/pinned snapshot/latest candidate/latest approved/source-truth paths changed |
| `git status --short --branch` | Only untracked review-only packet under `docs/hq/rookie_model/` before staging |
