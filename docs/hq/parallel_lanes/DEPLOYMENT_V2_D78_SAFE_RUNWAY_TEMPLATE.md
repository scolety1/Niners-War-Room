# Deployment V2 D78 Safe Runway Template

Use this template for a 5-10 task Deployment V2 runway.

## Runway Header

```text
Repo: C:\NWR\Niners-War-Room-deploy-v2
Branch: work/deployment-v2-discovery
Accepted baseline: <full-hash>
Task range: DXX-DYY
```

## Core Stance

- V1 remains `local_only`.
- Hosted deployment remains blocked.
- No deploy command exists.
- Deployment V2 is not the operator app path.
- Normal operator app path remains `C:\NWR\Niners-War-Room-outcome`.
- Normal operator branch remains `main`.

## Hard Guardrails

- Do not deploy.
- Do not create deploy commands.
- Do not expose public ports.
- Do not create secrets or credentials.
- Do not add CI/CD deploy workflows.
- Do not create containers/images.
- Do not alter Outcome runtime/app behavior.
- Do not touch other lane worktrees.
- Do not commit `data/`, `local_exports/`, `.venv/`, caches, logs, generated artifacts, archives, or secrets.
- Do not make hosted deployment ready.
- Do not create zip exports unless explicitly approved.

## Task Format

For each task, include:

- task id
- value
- allowed files
- rules
- validation commands
- commit message

## Stop Conditions

Stop only for a real blocker:

- wrong branch
- dirty repo before work
- baseline not in history
- failed validation that cannot be fixed within allowed scope
- request to cross a hard guardrail
- Python unavailable for script/test work, unless continuing docs-only is explicitly allowed

## Validation Gate

Use safe validation only:

```powershell
git status --short
git diff --check
python scripts/validate_local_only_surface_guard.py
python scripts/validate_local_only_surface_guard.py --report
python scripts/run_deployment_v2_readiness_checks.py --all
python scripts/audit_deployment_v2_docs_consistency.py
```

## Commit Rule

Prefer one commit per completed task. Commit only after validation for that task passes or the only non-GREEN signal is the expected dirty status from the task files before commit.

## Final Report

Return branch, starting HEAD, ending HEAD, commits, files changed, validations, local-only guard result, report mode result, readiness result, docs audit result, transcript result if run, deploy-surface confirmation, other-lane confirmation, remaining blockers, and final verdict.
