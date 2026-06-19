# Deployment V2 D45 Validation Inventory Manifest

## Scope

This manifest lists Deployment V2 validation surfaces. It is documentation only. It does not approve hosted deployment, create deploy commands, add CI/CD, create containers/images, expose public ports, create secrets, route production traffic, create zip exports, or change app/runtime behavior.

## Current Baseline

Accepted GREEN baseline before this D82 refresh:

```text
5ab091cbaa224c171d630aa9dc76761823123a0c
```

V1 remains `local_only`. Hosted deployment remains blocked. No deploy command exists. Deployment V2 is not the operator app path.

## Validation Scripts And Modes

| Surface | Command | Purpose | Expected verdict |
| --- | --- | --- | --- |
| Local-only guard | `python scripts/validate_local_only_surface_guard.py` | Detect forbidden deploy surfaces | GREEN |
| Guard report mode | `python scripts/validate_local_only_surface_guard.py --report` | Emit machine-readable guard summary | GREEN |
| Readiness runner | `python scripts/run_deployment_v2_readiness_checks.py` | Combine branch, HEAD, status, diff, guard, optional import, optional baseline, and docs audit checks | GREEN |
| Readiness JSON mode | `python scripts/run_deployment_v2_readiness_checks.py --json` | Emit machine-readable readiness summary | GREEN |
| Readiness all-checks mode | `python scripts/run_deployment_v2_readiness_checks.py --all` | Add every available safe validation layer, including schema smoke tests | GREEN when worktree is clean |
| Readiness baseline mode | `python scripts/run_deployment_v2_readiness_checks.py --baseline <accepted-baseline-commit>` | Verify HEAD descends from accepted baseline | GREEN when descendant and clean |
| Import report comparison | `python scripts/compare_deployment_v2_import_report.py <master-import-zip>` | Compare current lane to Master import zip when supplied | GREEN when report lineage matches |
| Import report JSON mode | `python scripts/compare_deployment_v2_import_report.py <master-import-zip> --json` | Emit machine-readable import comparison | GREEN/YELLOW/RED as comparison requires |
| Docs consistency audit | `python scripts/audit_deployment_v2_docs_consistency.py` | Confirm local-only/path/blocker docs consistency | GREEN with notes allowed |
| Docs audit JSON mode | `python scripts/audit_deployment_v2_docs_consistency.py --json` | Emit required/missing/note/blocked-language buckets | GREEN with notes allowed |
| Transcript printer | `python scripts/print_deployment_v2_operator_transcript.py` | Print compact HQ validation transcript | GREEN |
| Transcript JSON mode | `python scripts/print_deployment_v2_operator_transcript.py --json` | Emit machine-readable transcript | GREEN |
| Transcript all-checks mode | `python scripts/print_deployment_v2_operator_transcript.py --all` | Use readiness all-checks mode inside transcript | GREEN when worktree is clean |
| Baseline ancestry verifier | `python scripts/verify_deployment_v2_baseline_ancestry.py <accepted-baseline-commit>` | Verify current HEAD descends from baseline | GREEN |
| Baseline ancestry JSON mode | `python scripts/verify_deployment_v2_baseline_ancestry.py <accepted-baseline-commit> --json` | Emit machine-readable baseline validation | GREEN |

## Focused Tests

| Test file | Purpose | Expected verdict |
| --- | --- | --- |
| `tests/test_deployment_v2_local_only_surface_guard.py` | Guard clean path, blocked temp fixtures, report mode, and false-positive checks | PASS |
| `tests/test_deployment_v2_import_report_comparison.py` | Import helper parsing, JSON, and edge cases | PASS |
| `tests/test_deployment_v2_readiness_runner.py` | Runner verdict, JSON/report, baseline, and all-checks behavior | PASS |
| `tests/test_deployment_v2_docs_consistency_audit.py` | Docs audit required language, blocked wording, and operator path coverage | PASS |
| `tests/test_deployment_v2_operator_transcript.py` | Transcript stdout, JSON, baseline, and all-checks coverage | PASS |
| `tests/test_deployment_v2_baseline_ancestry.py` | Baseline ancestry verifier coverage | PASS |
| `tests/test_deployment_v2_validation_report_schemas.py` | JSON/report schema smoke coverage | PASS |

## Docs Audit Surface

Default docs audit scope:

```text
docs/hq/parallel_lanes/DEPLOYMENT_V2*.md
```

The audit must not scan other lane worktrees by default. Historical Vacation-path notes are allowed only as notes when current desktop-era operator path documentation is present.

## Current Posture

V1 remains `local_only`.

Hosted deployment remains BLOCKED.

No deploy command, CI/CD workflow, container/image, public route, public tunnel, hosted smoke plan, secret, credential, zip export, or production runtime path is approved.
