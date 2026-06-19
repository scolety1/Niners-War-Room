# Deployment V2 D76 Operator Quick Reference

## Current Stance

V1 remains `local_only`. Hosted deployment remains blocked. No deploy command exists. Deployment V2 is not the operator app path.

## Lane

- Repo: `C:\NWR\Niners-War-Room-deploy-v2`
- Branch: `work/deployment-v2-discovery`

## Normal Operator App

- Path: `C:\NWR\Niners-War-Room-outcome`
- Branch: `main`

## Safe Validation Commands

```powershell
git branch --show-current
git rev-parse HEAD
git status --short
git diff --check
python scripts/validate_local_only_surface_guard.py
python scripts/validate_local_only_surface_guard.py --report
python scripts/run_deployment_v2_readiness_checks.py
python scripts/run_deployment_v2_readiness_checks.py --all
python scripts/audit_deployment_v2_docs_consistency.py
python scripts/print_deployment_v2_operator_transcript.py --all
```

## Hard Blocked Surfaces

- deploy commands
- CI/CD deploy workflows
- containers/images
- public ports/routing
- secrets/credentials
- hosted smoke plans
- production runtime behavior changes
- generated/data/local-only artifacts
- other-lane behavior changes

## Final Report Format

Include branch, starting HEAD, ending HEAD, commits, files changed, validation outputs, local-only guard result, report mode result, readiness result, docs audit result, transcript result, deploy-surface confirmation, other-lane confirmation, remaining blockers, and final verdict.

## Remaining Hosted Blockers

Hosted deployment remains BLOCKED pending hosted target, owner, secrets policy, data policy, access policy, rollback policy, deploy command policy, CI/CD policy, public/private routing policy, and hosted smoke plan.
