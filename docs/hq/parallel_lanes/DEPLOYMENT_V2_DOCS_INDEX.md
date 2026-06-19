# Deployment V2 Documentation Index

## Scope

This index maps Deployment V2 readiness docs, validation scripts, and focused
tests to their purposes. It is documentation only. It does not approve hosted
deployment, create deploy commands, add CI/CD, create containers/images, expose
public ports, create secrets, route production traffic, or change app/runtime
behavior.

## Current Baseline And Paths

Latest accepted GREEN baseline entering the D27-D34 runway:

```text
97516a993ef94c6dd03fd43d9829dd0e9a7c2983
```

Deployment V2 checkout:

```text
C:\NWR\Niners-War-Room-deploy-v2
```

The Deployment V2 checkout is not the operator app path.

Normal local operator app path:

```text
C:\NWR\Niners-War-Room-outcome
```

Normal local operator branch:

```text
main
```

V1 remains `local_only`. Hosted deployment remains blocked.

## Baseline And Readiness Docs

| File | Purpose |
|---|---|
| `DEPLOYMENT_V2_D18_BRANCH_READINESS_CHECKLIST.md` | Required branch, HEAD, status, diff, guard, and import-report checks before any GREEN claim |
| `DEPLOYMENT_V2_D22_READINESS_AUTOMATION_BRIDGE.md` | Connects D18, guard report mode, and import comparison into a repeatable readiness process |
| `DEPLOYMENT_V2_D27_READ_ONLY_READINESS_RUNNER.md` | Documents the combined read-only readiness runner |
| `DEPLOYMENT_V2_D30_VERDICT_VOCABULARY_STANDARD.md` | Standardizes GREEN/YELLOW/RED/BLOCKED/SKIPPED/PASS/FAIL vocabulary |

## Guard And Report Docs

| File | Purpose |
|---|---|
| `DEPLOYMENT_V2_D17_DISCOVERY_GUARDRAIL_VALIDATION.md` | Introduces the local-only surface guard |
| `DEPLOYMENT_V2_D19_LOCAL_ONLY_GUARD_REPORT_MODE.md` | Defines guard JSON report fields |
| `DEPLOYMENT_V2_D20_LOCAL_ONLY_GUARD_REPORT_MODE.md` | Provides operator examples for text and JSON guard modes |

## Import Comparison Docs

| File | Purpose |
|---|---|
| `DEPLOYMENT_V2_D21_IMPORT_REPORT_COMPARISON_HELPER.md` | Documents the read-only Master import zip comparison helper |
| `DEPLOYMENT_V2_D29_IMPORT_HELPER_EDGE_CASE_HARDENING.md` | Documents missing/invalid/incomplete import report edge-case behavior |

## Forbidden Surface Docs

| File | Purpose |
|---|---|
| `DEPLOYMENT_V2_D14_HOSTED_DEPLOYMENT_BLOCKER_CONTRACT.md` | Records hosted deployment as blocked and enumerates future approval needs |
| `DEPLOYMENT_V2_D24_FORBIDDEN_SURFACE_CATALOG.md` | Catalogs forbidden deployment, CI/CD, container, route, secret, hosted smoke, and runtime surfaces |
| `DEPLOYMENT_V2_D23_DESKTOP_OPERATOR_PATH_RECONCILIATION.md` | Clarifies that the desktop operator path is `C:\NWR\Niners-War-Room-outcome` and the Deployment V2 checkout is not the app path |

## Closeout Docs

| File | Purpose |
|---|---|
| `DEPLOYMENT_V2_D26_SAFE_RUNWAY_CLOSEOUT.md` | Summarizes D19-D25 validation-hardening runway |

## Validation Scripts

| Script | Purpose |
|---|---|
| `scripts/validate_local_only_surface_guard.py` | Read-only local-only guard for forbidden deploy surfaces |
| `scripts/compare_deployment_v2_import_report.py` | Read-only comparison of current lane state to a Master import verification zip |
| `scripts/run_deployment_v2_readiness_checks.py` | Read-only combined readiness runner for branch, HEAD, status, diff, guard, and optional import comparison |

## Focused Tests

| Test | Purpose |
|---|---|
| `tests/test_deployment_v2_local_only_surface_guard.py` | Guard clean-path, report-shape, blocked-surface, skipped-dir, and false-positive coverage |
| `tests/test_deployment_v2_import_report_comparison.py` | Import-report parsing, comparison, and edge-case coverage |
| `tests/test_deployment_v2_readiness_runner.py` | Readiness runner verdict and report behavior coverage |

## Blocked Work

Hosted deployment remains BLOCKED until HQ approves target, owner, secrets
policy, data policy, access policy, rollback policy, deploy command policy,
CI/CD policy, public/private routing policy, and hosted smoke plan.

No local-only validation GREEN claim changes that hosted blocker.
