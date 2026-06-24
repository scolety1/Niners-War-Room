# NWR Full Safe Data Loader V1 - 2026-06-24

## 1. Starting HEAD

- Branch created from `origin/work/hq-parallel-control`.
- Starting HEAD: `9924e6d60bd7e210f112a3887142fc37f47705e1`.
- Base repo was clean, synchronized, and had no unmerged index entries before the worktree was created.

## 2. Source Registry Design

Implemented one registry in `src/services/data_refresh_orchestrator_service.py`.

Each source declares:

- `source_id`, `source_name`, `source_kind`
- `loader_category`
- quick/full eligibility flags
- API key and required env vars
- runner/configuration/safety flags
- protected/manual/cache/tracked-artifact policy
- expected artifacts and freshness policy
- model-use permission and warning
- default action, failure mode, and user explanation

The registry is intentionally policy-first. Loader modes select from the registry; the UI no longer owns scattered refresh rules.

## 3. Loader Modes Implemented

- `QUICK_REFRESH`
- `FULL_SAFE_REFRESH`
- `CHECK_PROTECTED_ARTIFACTS`
- `MANUAL_SOURCES_CHECKLIST`

Result rows include `run_id`, `run_timestamp`, `loader_mode`, `source_id`, `source_name`, `loader_category`, `action_type`, `refreshed`, `configured`, `freshness`, `expected_artifacts`, `found_artifacts`, `user_explanation`, and `model_use_warning`.

## 4. Quick Refresh Behavior

Quick Refresh pulls only:

- Sleeper league data
- DynastyProcess market baseline

It also performs cheap protected checks for frozen board, pinned hash, and latest candidate/approved status. It does not run nflverse, CFBD, vendor, Gmail, model, Outcome, PDF, ADP, or runtime refreshes.

## 5. Full Safe Refresh Behavior

Full Safe Refresh means "pull every approved eligible current source."

It includes:

- Sleeper league data
- DynastyProcess market baseline
- nflverse when `scripts/run_nflverse_refresh_v0.ps1` exists
- CFBD only when `CFBD_API_KEY` is configured

It also reports check-only and manual-blocked sources. It does not mutate model/rank/candidate/frozen/latest/pinned outputs.

## 6. Check-Only / Protected Behavior

Check-only sources are status/freshness checks only:

- Frozen Final Draft Board V1
- pinned manifest/hash
- latest_candidate/latest_approved
- full dynasty/model_v4 output
- Outcome artifacts
- LVE PDF/free-agent extract
- runtime draft state
- model evaluation harness outputs
- Sleeper ADP display context

Frozen board wording remains baseline/checkpoint, not source truth.

## 7. Manual / Blocked Behavior

Manual checklist sources are never pulled:

- Gmail league-history evidence
- RotoWire/vendor exports
- FantasyPros/vendor/projection exports
- PDFs/manual evidence files

The loader reports `BLOCKED_MANUAL` with user-facing explanations instead of scraping, pulling raw email bodies, or importing vendor exports.

## 8. nflverse Behavior

nflverse is `AUTO_SLOW`.

- Runner: `scripts/run_nflverse_refresh_v0.ps1`
- Included in Full Safe Refresh only
- Not included in Quick Refresh
- Uses the existing runner without `-WriteCandidates`
- Raw/cache output remains outside git under shared ingest paths
- No model/rank/candidate writes are made by this loader

## 9. CFBD Behavior With And Without API Key

Without `CFBD_API_KEY`:

- Source category is `NOT_CONFIGURED`
- Full Safe Refresh reports `NOT_CONFIGURED`
- The UI explains why CFBD may be unavailable

With `CFBD_API_KEY`:

- Source category becomes `AUTO_SLOW`
- Full Safe Refresh can run the safe CFBD probe
- Raw CFBD data is cached outside git under `C:\NWR_SHARED_DATA\public_sources\cfbd`
- Local manifest/status output is written under ignored refresh status paths
- Identity-gate warning is attached: CFBD identities must be reviewed before model use
- CFBD is not made model input in this task
- College/rookie data is not invented if unavailable

## 10. What Still Does Not Become Model Input

The loader does not make these model input:

- DynastyProcess
- ADP
- vendor exports
- proxy data
- CFBD
- Gmail evidence
- refreshed Sleeper league state
- nflverse raw/cache data from this refresh

No source writes model/rank/candidate outputs.

## 11. Tests / Checks

Passed:

- Focused pytest: `tests/test_data_refresh_orchestrator_service.py tests/test_data_health_dashboard_service.py`
- Ruff on touched Python files
- Python compile on touched Python files
- `git diff --check`
- Frozen board row guardrail: `66` rows
- Pinned hash guardrail: `5780156F09FBDA61FB906715C7341DB1B6D320C8D8EFA588070F19C4C50F45CE`
- No `C:\NWR_SHARED_DATA`/raw CFBD/nflverse/vendor/Gmail cache paths tracked
- Diff contains no frozen/latest/pinned/model output artifacts

## 12. Browser / Export Proof

Browser smoke:

- `http://localhost:8507/refresh-data`
  - Quick Refresh button visible
  - Full Safe Refresh button visible
  - Check Protected Artifacts button visible
  - Manual Sources Checklist button visible
  - CFBD/API-key explanation visible
  - Refreshed-data-not-model-output policy visible
  - Manual checklist run showed run summary and Export Results button

- `http://localhost:8507/settings-data-health`
  - Safe Data Loader section visible
  - Quick/Full/Protected/Manual controls visible
  - Policy copy visible
  - Refresh Data Run Status still visible

Ignored proof exports:

- `local_exports/safe_loader_proof_20260624/20260624_225036_quick_refresh_results.csv`
- `local_exports/safe_loader_proof_20260624/20260624_225036_full_safe_refresh_results.csv`
- `local_exports/safe_loader_proof_20260624/20260624_225036_check_protected_artifacts_results.csv`
- `local_exports/safe_loader_proof_20260624/20260624_225037_manual_sources_checklist_results.csv`

Proof runs used deterministic handlers for external pull steps to avoid a surprise slow ingest during validation; check-only and manual policy paths ran normally.

## 13. Remaining Gaps

- CFBD safe probe requires a real `CFBD_API_KEY` for live verification.
- Full Safe Refresh live nflverse runtime depends on the existing local runner environment.
- Proof exports are ignored local artifacts and are not committed.
- The loader intentionally does not promote refreshed data into model inputs; future lanes must approve any separate admission workflow.

## 14. Connector Completion Update

### 1. nflverse Connector Status

Status: connector-ready with dependency gating.

- Confirmed runner: `scripts/run_nflverse_refresh_v0.ps1`
- Added `-CheckDependencies` to the runner for non-mutating dependency checks.
- Full Safe Refresh includes nflverse only when the runner exists and the local deps path exists:
  `C:\NWR_SHARED_DATA\vendor_spikes\nflverse\scratch\pydeps`
- Missing runner/deps returns `NOT_CONFIGURED` with a clear explanation.
- Post-run status includes runner path, start/end time, exit code, expected artifacts, found artifacts, freshness, user explanation, raw cache location, and model-use warning.
- Loader invokes the runner without `-WriteCandidates`; no candidate/model/ranking outputs are written.
- Raw/cache output remains outside git.

### 2. CFBD Connector Status

Status: minimum safe connector V1 implemented.

- Uses existing config/env field: `CFBD_API_KEY`
- Raw/cache location: `C:\NWR_SHARED_DATA\public_sources\cfbd\`
- Writes ignored local status artifacts under `local_exports/refresh_data/cfbd/latest/`
- Writes and validates `cfbd_review_status.csv`
- Attaches identity gate: `CFBD player identities must be reviewed/matched before model use.`
- Does not make CFBD model input.
- Does not invent college/rookie data when source data is unavailable.

### 3. Behavior With CFBD_API_KEY Absent

- `loader_category = NOT_CONFIGURED`
- `action_type = NOT_CONFIGURED`
- `refreshed = false`
- `user_explanation = "CFBD_API_KEY is not set; CFBD refresh is unavailable."`
- No live network call is attempted.

### 4. Behavior With CFBD_API_KEY Present / Mocked

Focused tests mock the CFBD HTTP path. With a mocked key and mocked response:

- CFBD refresh runs automatically in Full Safe Refresh.
- Raw JSON is written only under the outside-git shared cache root.
- `cfbd_refresh_manifest.json` is written under ignored local refresh status.
- `cfbd_review_status.csv` is written and schema-validated.
- `model_use_allowed` remains `false`.
- The result row reports review/status output only and repeats the identity-gate warning.

### 5. Remaining Connector Gaps

- Live CFBD verification still requires a real `CFBD_API_KEY`.
- Live nflverse execution depends on the existing local deps path and package environment.
- The loader deliberately stops at cache/status/review artifacts; it does not include admission, promotion, or model-input wiring.

### 6. Proof No Model / Rank / Source-Truth Mutation Occurs

Validation confirmed:

- Frozen board remains 66 rows.
- Pinned hash remains unchanged.
- No `latest_candidate` or `latest_approved` files are touched.
- No `final_board_rank`, Dynasty Rank, Candidate Rank, tier assignment, model output, or rank logic file is changed.
- No `C:\NWR_SHARED_DATA` files are tracked.
- No raw nflverse/CFBD/vendor/Gmail files are tracked.
- Full Safe Refresh result rows now expose `tracked_artifacts_written`; connector refreshes leave it blank.

Connector proof exports, all ignored:

- `local_exports/safe_loader_connector_proof_20260624/20260624_230446_quick_refresh_results.csv`
- `local_exports/safe_loader_connector_proof_20260624/20260624_230446_full_safe_refresh_results.csv`
- `local_exports/safe_loader_connector_proof_20260624/20260624_230446_check_protected_artifacts_results.csv`
- `local_exports/safe_loader_connector_proof_20260624/20260624_230446_manual_sources_checklist_results.csv`
