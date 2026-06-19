# Deployment V2 Documentation Index

## Scope

This index maps Deployment V2 readiness docs, validation scripts, and focused tests to their purposes. It is documentation only. It does not approve hosted deployment, create deploy commands, add CI/CD, create containers/images, expose public ports, create secrets, route production traffic, or change app/runtime behavior.

## Current Baseline And Paths

Latest accepted GREEN baseline before this D81 refresh:

```text
960cd6322f8fdf0d5ee63b996b65fb0c11f87106
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

V1 remains `local_only`. Hosted deployment remains blocked. No deploy command exists.

## Baseline And Readiness Docs

| File | Purpose |
| --- | --- |
| `DEPLOYMENT_V2_D18_BRANCH_READINESS_CHECKLIST.md` | Required branch, HEAD, status, diff, guard, and import-report checks before any GREEN claim |
| `DEPLOYMENT_V2_D22_READINESS_AUTOMATION_BRIDGE.md` | Connects checklist, guard report mode, and import comparison into a repeatable readiness process |
| `DEPLOYMENT_V2_D27_READ_ONLY_READINESS_RUNNER.md` | Documents the combined read-only readiness runner |
| `DEPLOYMENT_V2_D30_VERDICT_VOCABULARY_STANDARD.md` | Standardizes GREEN/YELLOW/RED/BLOCKED/SKIPPED/PASS/FAIL vocabulary |
| `DEPLOYMENT_V2_D45_VALIDATION_INVENTORY_MANIFEST.md` | Inventories Deployment V2 validation scripts, tests, and audit surfaces |
| `DEPLOYMENT_V2_D56_BASELINE_ANCESTRY_VERIFIER.md` | Documents the read-only baseline ancestry verifier |
| `DEPLOYMENT_V2_D58_READINESS_BASELINE_CHECK.md` | Documents optional readiness baseline validation |
| `DEPLOYMENT_V2_D70_VALIDATION_AGGREGATION_GUIDE.md` | Explains how validation layers combine before GREEN claims |
| `DEPLOYMENT_V2_D71_READINESS_ALL_CHECKS_MODE.md` | Documents readiness runner all-checks mode |

## Guard And Report Docs

| File | Purpose |
| --- | --- |
| `DEPLOYMENT_V2_D17_DISCOVERY_GUARDRAIL_VALIDATION.md` | Introduces the local-only surface guard |
| `DEPLOYMENT_V2_D19_LOCAL_ONLY_GUARD_REPORT_MODE.md` | Defines guard JSON report fields |
| `DEPLOYMENT_V2_D20_LOCAL_ONLY_GUARD_REPORT_MODE.md` | Provides operator examples for text and JSON guard modes |
| `DEPLOYMENT_V2_D46_READINESS_RUNNER_DOCS_AUDIT_SUMMARY.md` | Documents docs-audit summary in readiness output |
| `DEPLOYMENT_V2_D48_TRANSCRIPT_JSON_OUTPUT.md` | Documents transcript JSON output |
| `DEPLOYMENT_V2_D49_IMPORT_HELPER_JSON_OUTPUT.md` | Documents import helper JSON output |
| `DEPLOYMENT_V2_D53_DOCS_AUDIT_JSON_OUTPUT.md` | Documents docs audit JSON output |
| `DEPLOYMENT_V2_D59_TRANSCRIPT_BASELINE_CHECK.md` | Documents baseline information in transcripts |
| `DEPLOYMENT_V2_D60_VALIDATION_REPORT_SCHEMA_REFERENCE.md` | Defines JSON/report schemas for validation tools |

## Import Comparison Docs

| File | Purpose |
| --- | --- |
| `DEPLOYMENT_V2_D21_IMPORT_REPORT_COMPARISON_HELPER.md` | Documents the read-only Master import zip comparison helper |
| `DEPLOYMENT_V2_D29_IMPORT_HELPER_EDGE_CASE_HARDENING.md` | Documents missing/invalid/incomplete import report edge-case behavior |

## Forbidden Surface And Path Docs

| File | Purpose |
| --- | --- |
| `DEPLOYMENT_V2_D14_HOSTED_DEPLOYMENT_BLOCKER_CONTRACT.md` | Records hosted deployment as blocked and enumerates future approval needs |
| `DEPLOYMENT_V2_D23_DESKTOP_OPERATOR_PATH_RECONCILIATION.md` | Clarifies desktop operator path and says Deployment V2 is not the app path |
| `DEPLOYMENT_V2_D24_FORBIDDEN_SURFACE_CATALOG.md` | Catalogs forbidden deployment, CI/CD, container, route, secret, hosted smoke, and runtime surfaces |
| `DEPLOYMENT_V2_D51_GUARD_PATTERN_MANIFEST.md` | Maps forbidden-surface categories to guard/test coverage |
| `DEPLOYMENT_V2_D63_SAFE_VALIDATION_COMMAND_CATALOG.md` | Catalogs safe validation-only commands |
| `DEPLOYMENT_V2_D64_OPERATOR_ESCALATION_MATRIX.md` | Defines escalation outcomes for common validation conditions |
| `DEPLOYMENT_V2_D66_GUARD_FALSE_POSITIVE_REVIEW.md` | Explains safe docs language versus forbidden deploy-surface language |
| `DEPLOYMENT_V2_D74_VALIDATION_FAILURE_EXAMPLES.md` | Gives safe failure-report examples without executable deploy instructions |

## Operator Templates And Policies

| File | Purpose |
| --- | --- |
| `DEPLOYMENT_V2_D32_OPERATOR_TRANSCRIPT_TEMPLATE.md` | Provides fill-in transcript structure |
| `DEPLOYMENT_V2_D76_OPERATOR_QUICK_REFERENCE.md` | Concise operator reference |
| `DEPLOYMENT_V2_D77_HQ_RESTART_PROMPT_TEMPLATE.md` | Restart prompt template for future HQ sessions |
| `DEPLOYMENT_V2_D78_SAFE_RUNWAY_TEMPLATE.md` | Template for 5-10 task safe runways |
| `DEPLOYMENT_V2_D79_CHAINED_RUNWAY_POLICY.md` | Policy for chaining multiple safe runways |

## Artifact And Closeout Docs

| File | Purpose |
| --- | --- |
| `DEPLOYMENT_V2_D26_SAFE_RUNWAY_CLOSEOUT.md` | Summarizes D19-D25 |
| `DEPLOYMENT_V2_D34_SECOND_SAFE_RUNWAY_CLOSEOUT.md` | Summarizes D27-D33 |
| `DEPLOYMENT_V2_D44_THIRD_SAFE_RUNWAY_CLOSEOUT.md` | Summarizes D35-D43 |
| `DEPLOYMENT_V2_D55_FOURTH_SAFE_RUNWAY_CLOSEOUT.md` | Summarizes D45-D54 |
| `DEPLOYMENT_V2_D62_FIFTH_SAFE_RUNWAY_CLOSEOUT.md` | Summarizes D56-D61 |
| `DEPLOYMENT_V2_D69_SIXTH_SAFE_RUNWAY_CLOSEOUT.md` | Summarizes D63-D68 |
| `DEPLOYMENT_V2_D75_SEVENTH_SAFE_RUNWAY_CLOSEOUT.md` | Summarizes D70-D74 |
| `DEPLOYMENT_V2_D80_EIGHTH_SAFE_RUNWAY_CLOSEOUT.md` | Summarizes D76-D79 |
| `DEPLOYMENT_V2_D33_DATA_GENERATED_ARTIFACT_EXCLUSION_AUDIT.md` | Documents generated/data/local-only artifact exclusions |

## Validation Scripts

| Script | Purpose |
| --- | --- |
| `scripts/validate_local_only_surface_guard.py` | Read-only local-only guard for forbidden deploy surfaces |
| `scripts/compare_deployment_v2_import_report.py` | Read-only comparison of current lane state to a Master import verification zip |
| `scripts/run_deployment_v2_readiness_checks.py` | Read-only combined readiness runner with optional import, baseline, JSON, and all-checks modes |
| `scripts/audit_deployment_v2_docs_consistency.py` | Read-only docs consistency audit |
| `scripts/print_deployment_v2_operator_transcript.py` | Read-only transcript printer with JSON and all-checks modes |
| `scripts/verify_deployment_v2_baseline_ancestry.py` | Read-only baseline ancestry verifier |

## Focused Tests

| Test | Purpose |
| --- | --- |
| `tests/test_deployment_v2_local_only_surface_guard.py` | Guard clean-path, report-shape, blocked-surface, skipped-dir, and false-positive coverage |
| `tests/test_deployment_v2_import_report_comparison.py` | Import-report parsing, comparison, JSON, and edge-case coverage |
| `tests/test_deployment_v2_readiness_runner.py` | Readiness runner verdict, JSON, baseline, and all-checks coverage |
| `tests/test_deployment_v2_docs_consistency_audit.py` | Docs audit required-language, hosted-readiness, and path-reference coverage |
| `tests/test_deployment_v2_operator_transcript.py` | Transcript human, JSON, baseline, and all-checks coverage |
| `tests/test_deployment_v2_baseline_ancestry.py` | Baseline ancestry verifier coverage |
| `tests/test_deployment_v2_validation_report_schemas.py` | JSON/report schema smoke tests |

## Blocked Work

Hosted deployment remains BLOCKED until HQ approves hosted target, owner, secrets policy, data policy, access policy, rollback policy, deploy command policy, CI/CD policy, public/private routing policy, and hosted smoke plan.

No local-only validation GREEN claim changes that hosted blocker.
