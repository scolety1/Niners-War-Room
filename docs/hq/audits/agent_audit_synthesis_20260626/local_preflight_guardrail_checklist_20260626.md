# Local Preflight Guardrail Checklist - 2026-06-26

Purpose: run this before any future lane that might touch app wiring, data refreshes, model outputs, or review evidence. This checklist is intentionally conservative and should be run before Live Draft V2 implementation work.

## Required focused checks

```powershell
pytest tests/test_agent_audit_synthesis_guardrails.py tests/test_agent_audit_followup_guardrails.py tests/test_evidence_status_registry.py -q
```

Run lane-specific tests for any touched service/page. Examples:

```powershell
pytest tests/test_data_refresh_orchestrator_service.py tests/test_data_health_dashboard_service.py -q
pytest tests/test_draft_day_runtime_state_service.py tests/test_draft_day_workflow_service.py -q
pytest tests/test_player_compare_decision_service.py tests/test_draft_day_trade_lab_service.py -q
```

## Ruff

Run Ruff on touched Python files first:

```powershell
ruff check tests/test_agent_audit_synthesis_guardrails.py tests/test_agent_audit_followup_guardrails.py
```

Full-repo Ruff can be run as an informational check, but this repo currently has older pre-existing style debt outside the audit lane. Do not treat unrelated legacy findings as permission to refactor broadly.

## Protected artifact diff

```powershell
git diff --stat -- data docs src app tests
git diff --name-only | Select-String -Pattern "latest_candidate|latest_approved|pinned|Frozen|final_board_rank|Dynasty Rank"
```

Expected result: no protected source-truth/rank/model artifact changes unless a lane explicitly authorized them. For this audit lane, the expected result is no protected artifact mutation.

## Raw/shared/local/export/secret tracking scan

Literal protected local paths: `C:\NWR_SHARED_DATA`, `C:\NWR_LOCAL_SECRETS`, and `local_exports`.

```powershell
git ls-files | Select-String -Pattern "C:\\NWR_SHARED_DATA|C:\\NWR_LOCAL_SECRETS|local_exports|runtime.*\\.json|api_key|secret|token|raw|cache"
```

Expected result: no tracked shared/local secret/runtime/raw cache files. Investigate any hit before committing.

## Blocked-field scanner

Run the audit follow-up guardrail tests:

```powershell
pytest tests/test_agent_audit_followup_guardrails.py -q
```

This verifies:

- CFBD, NFL usage, Outcome, DynastyProcess, and proxy evidence keep model/training/app-wiring gates closed.
- True routes, true TPRR, and true YPRR remain blocked licensed-data gaps.
- Decision pages do not read CFBD/NFL/full-refresh evidence roots.
- Missing age, injury/status, outcome, and player_id remain `Not enough information` or blocked, never zero/average/healthy/clean/low-risk.

## Absolute path scan

Absolute local paths are allowed in docs as references, but they should not become app/runtime dependencies or tracked raw data pointers.

```powershell
rg "C:\\\\NWR_SHARED_DATA|C:\\\\NWR_LOCAL_SECRETS|local_exports" app src tests docs/hq -g "!docs/hq/audits/agent_audit_synthesis_20260626/local_preflight_guardrail_checklist_20260626.md"
```

Investigate any app/src/test hit. Docs-only references should clearly say untracked/local-only.

## Git whitespace

```powershell
git diff --check
```

Expected result: no whitespace errors.

## Stop conditions

Stop before implementation if any check suggests:

- model input enabled for CFBD/NFL usage/proxy/market/Outcome evidence;
- decision-page wiring enabled from review-only evidence;
- missing data coerced to zero, average, healthy, clean, or low-risk;
- protected rank/source-truth artifacts changed;
- raw/shared/local secret/runtime files tracked;
- hosted deployment work started.
