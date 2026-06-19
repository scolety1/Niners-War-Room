# Deployment V2 D70 Validation Aggregation Guide

Deployment V2 GREEN claims must be assembled from layered read-only validation, not from a single check.

V1 remains `local_only`. Hosted deployment remains blocked. No deploy command exists. Deployment V2 is not the operator app path.

## Validation Layers

1. Git branch/head/status
2. `git diff --check`
3. Local-only guard human output
4. Local-only guard report output
5. Readiness runner
6. Import helper when a Master import zip is supplied
7. Docs consistency audit
8. Transcript printer
9. Baseline ancestry verifier when a baseline is supplied
10. Focused Deployment V2 tests

## Aggregation Rule

- Any RED validation layer makes the overall lane claim RED until fixed within allowed scope.
- Any missing optional comparison is SKIPPED unless the user explicitly required it.
- Historical-path NOTE findings remain GREEN when D23 or later docs identify the desktop-era operator path.
- Local-only validation GREEN does not imply hosted deployment readiness.
- Hosted deployment remains BLOCKED until all hosted blockers are explicitly approved.

## Required GREEN Claim Checklist

Before a Deployment V2 GREEN claim, confirm:

- current branch is `work/deployment-v2-discovery`
- current HEAD descends from the accepted baseline when a baseline is supplied
- `git status --short` is clean
- `git diff --check` is clean
- local-only guard normal mode is GREEN
- local-only guard report mode is GREEN
- readiness runner is GREEN
- docs audit is GREEN or GREEN with notes only
- focused tests pass when Python is available

## Remaining Hosted Blockers

Hosted deployment remains BLOCKED pending hosted target, owner, secrets policy, data policy, access policy, rollback policy, deploy command policy, CI/CD policy, public/private routing policy, and hosted smoke plan.
