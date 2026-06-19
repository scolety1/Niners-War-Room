# Deployment V2 D45 Validation Inventory Manifest

## Scope

This manifest lists Deployment V2 validation surfaces. It is documentation only.
It does not approve hosted deployment, create deploy commands, add CI/CD,
create containers/images, expose public ports, create secrets, route production
traffic, create zip exports, or change app/runtime behavior.

## Current Baseline

Accepted GREEN baseline:

```text
a459044e049befc3d5fef5fcd9e147fc271c168e
```

## Validation Scripts

| Surface | Path | Purpose | Expected verdict |
|---|---|---|---|
| Local-only guard | `scripts/validate_local_only_surface_guard.py` | Detect forbidden deploy surfaces | GREEN |
| Guard report mode | `scripts/validate_local_only_surface_guard.py --report` | Emit machine-readable guard summary | GREEN |
| Readiness runner | `scripts/run_deployment_v2_readiness_checks.py` | Combine branch, HEAD, status, diff, guard, and optional import checks | GREEN |
| Readiness JSON mode | `scripts/run_deployment_v2_readiness_checks.py --json` | Emit machine-readable readiness summary | GREEN |
| Import report comparison | `scripts/compare_deployment_v2_import_report.py` | Compare current lane to Master import zip when supplied | GREEN when report lineage matches |
| Docs consistency audit | `scripts/audit_deployment_v2_docs_consistency.py` | Confirm local-only/path/blocker docs consistency | GREEN with historical-path NOTE allowed |
| Transcript printer | `scripts/print_deployment_v2_operator_transcript.py` | Print compact HQ validation transcript | GREEN |

## Focused Tests

| Test file | Purpose | Expected verdict |
|---|---|---|
| `tests/test_deployment_v2_local_only_surface_guard.py` | Guard clean path, blocked temp fixtures, report mode, and false-positive checks | PASS |
| `tests/test_deployment_v2_import_report_comparison.py` | Import helper parsing and edge cases | PASS |
| `tests/test_deployment_v2_readiness_runner.py` | Runner verdict and JSON/report behavior | PASS |
| `tests/test_deployment_v2_docs_consistency_audit.py` | Docs audit required language and blocked wording coverage | PASS |
| `tests/test_deployment_v2_operator_transcript.py` | Transcript stdout and optional temp output coverage | PASS |

## Docs Audit Surface

Default docs audit scope:

```text
docs/hq/parallel_lanes/DEPLOYMENT_V2*.md
```

The audit must not scan other lane worktrees by default.

## Current Posture

V1 remains `local_only`.

Hosted deployment remains BLOCKED.

No deploy command, CI/CD workflow, container/image, public route, public tunnel,
hosted smoke plan, secret, credential, zip export, or production runtime path is
approved.
