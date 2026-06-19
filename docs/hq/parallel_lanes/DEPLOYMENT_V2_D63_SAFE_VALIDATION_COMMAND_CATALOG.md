# Deployment V2 D63 Safe Validation Command Catalog

This catalog lists safe read-only validation commands for Deployment V2 operators.

These commands are validation-only. They do not deploy, serve, expose public ports, create credentials, add CI/CD, create containers/images, or change app behavior.

V1 remains `local_only`. Hosted deployment remains blocked. No deploy command exists. Deployment V2 is not the operator app path.

## Git State Checks

```powershell
git branch --show-current
git rev-parse HEAD
git rev-parse --short HEAD
git log -1 --oneline
git log --oneline -20
git status --short
git diff --check
```

## Local-Only Guard Checks

```powershell
python scripts/validate_local_only_surface_guard.py
python scripts/validate_local_only_surface_guard.py --report
```

## Readiness Runner Checks

```powershell
python scripts/run_deployment_v2_readiness_checks.py
python scripts/run_deployment_v2_readiness_checks.py --json
python scripts/run_deployment_v2_readiness_checks.py --baseline <accepted-baseline-commit>
```

## Import Report Comparison

```powershell
python scripts/compare_deployment_v2_import_report.py <master-import-zip>
python scripts/compare_deployment_v2_import_report.py <master-import-zip> --json
```

Use only a provided Master import verification zip. Do not create zip exports unless explicitly approved.

## Docs Consistency Audit

```powershell
python scripts/audit_deployment_v2_docs_consistency.py
python scripts/audit_deployment_v2_docs_consistency.py --json
```

## Transcript Printer

```powershell
python scripts/print_deployment_v2_operator_transcript.py
python scripts/print_deployment_v2_operator_transcript.py --json
python scripts/print_deployment_v2_operator_transcript.py --baseline <accepted-baseline-commit>
```

## Baseline Ancestry

```powershell
python scripts/verify_deployment_v2_baseline_ancestry.py <accepted-baseline-commit>
python scripts/verify_deployment_v2_baseline_ancestry.py <accepted-baseline-commit> --json
```

## Focused Tests

```powershell
python -m pytest tests/test_deployment_v2_local_only_surface_guard.py tests/test_deployment_v2_import_report_comparison.py tests/test_deployment_v2_readiness_runner.py tests/test_deployment_v2_docs_consistency_audit.py tests/test_deployment_v2_operator_transcript.py tests/test_deployment_v2_baseline_ancestry.py tests/test_deployment_v2_validation_report_schemas.py
```

## Blocked Command Classes

Operators must not add or run app launch, hosting, public routing, CI/CD, container/image, credential creation, or hosted smoke commands in this lane.
