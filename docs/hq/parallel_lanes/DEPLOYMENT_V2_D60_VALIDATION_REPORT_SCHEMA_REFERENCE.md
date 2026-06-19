# Deployment V2 D60 Validation Report Schema Reference

This reference describes Deployment V2 machine-readable validation reports. These reports are validation-only and do not imply hosted deployment readiness.

V1 remains `local_only`. Hosted deployment remains blocked. No deploy command exists. Deployment V2 is not the operator app path.

## Local-Only Guard Report

Command:

```powershell
python scripts/validate_local_only_surface_guard.py --report
```

Top-level fields:

- `verdict`: `GREEN` or `RED`.
- `root`: scanned repository root.
- `checked_path_count`: number of scanned files after skipped directories.
- `checked_categories`: blocked files, path segments, command-surface files, command patterns, and skipped directories.
- `blocked_surface_count`: number of blocked surfaces found.
- `reason_summary`: count by violation reason.
- `violations`: list of `{path, reason}` objects.

## Readiness Runner JSON

Command:

```powershell
python scripts/run_deployment_v2_readiness_checks.py --json
```

Top-level fields:

- `verdict`: aggregate `GREEN`, `YELLOW`, or `RED`.
- `branch`, `head`, `clean_status`, `diff_check`: git-state checks.
- `local_only_guard`, `guard_report`: guard checks.
- `import_report`: import comparison result or `SKIPPED`.
- `baseline_ancestry`: baseline check result or `SKIPPED`.
- `docs_audit`: docs consistency result.
- `skipped_checks`: skipped optional checks.
- `blockers`: RED/BLOCKED detail strings.
- `violations`: non-GREEN blocking check objects.
- `checks`: ordered list of all checks.

## Import Helper JSON

Command:

```powershell
python scripts/compare_deployment_v2_import_report.py <zip-path> --json
```

Top-level fields:

- `verdict`: `GREEN`, `YELLOW`, or `RED`.
- `reasons`: comparison reasons.
- `report_head`: report HEAD object or null.
- `current_head`: current HEAD object or null.
- `ancestor_or_match`: whether current HEAD matches or descends from report HEAD.
- `clean_status`: current clean-status object.
- `diff_check`: current diff-check object.

## Docs Audit JSON

Command:

```powershell
python scripts/audit_deployment_v2_docs_consistency.py --json
```

Top-level fields:

- `verdict`: docs consistency verdict.
- `required_phrases`: required local-only and operator-path language.
- `missing_phrases`: absent required language.
- `notes`: non-blocking notes.
- `blocked_language_hits`: hosted-readiness language violations.
- `historical_path_notes`: legacy path notes.
- `findings`: complete finding list.

## Transcript JSON

Command:

```powershell
python scripts/print_deployment_v2_operator_transcript.py --json
```

Top-level fields:

- `lane`: `Deployment V2`.
- `readiness_verdict`: readiness aggregate verdict.
- `final_verdict`: final operator transcript verdict.
- `branch`, `head`, `baseline_ancestry`: selected readiness summaries.
- `readiness`: readiness checks by name.
- `docs_consistency`: docs audit summary.
- `hosted_deployment`: always `BLOCKED`.
- `remaining_blockers`: hosted blocker list.
- `deploy_surface_added`: boolean.
- `other_lane_touched`: boolean.

## Baseline Ancestry JSON

Command:

```powershell
python scripts/verify_deployment_v2_baseline_ancestry.py <baseline-commit> --json
```

Top-level fields:

- `verdict`: `GREEN`, `YELLOW`, or `RED`.
- `baseline`: supplied baseline commit.
- `current_head`: `{full, short}` object.
- `ancestor`: whether current HEAD descends from baseline.
- `clean_required`: whether clean status was required.
- `clean_status`: clean status boolean or null.
- `status_short`: git status output when clean status was checked.
- `reasons`: explanatory reason strings.

## Hosted Deployment Status

Local validation `GREEN` means Deployment V2 discovery checks passed. Hosted deployment remains `BLOCKED` until hosted target, owner, secrets policy, data policy, access policy, rollback policy, deploy command policy, CI/CD policy, public/private routing policy, and hosted smoke plan are explicitly approved.
