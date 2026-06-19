# Deployment V2 D21 Import Report Comparison Helper

## Scope

This document records a read-only helper for comparing the current Deployment
V2 lane state to a Master import verification bundle. It does not approve hosted
deployment, create deploy commands, add CI/CD, create containers/images, expose
public ports, create secrets, route production traffic, or change app/runtime
behavior.

## Helper

Run from the Deployment V2 repo:

```powershell
python scripts\compare_deployment_v2_import_report.py "C:\NWR\_lane_import_checks\NWR_LANE_IMPORT_CHECK_20260618_222530.zip"
```

The helper reads the zip in memory and looks for:

```text
05_DEPLOYMENT_V2.md
```

It does not extract repository source, data, exports, archives, or generated
artifacts to disk.

## Compared Fields

The helper compares:

- expected branch
- current branch
- HEAD full hash
- HEAD short hash
- clean `git status --short`
- clean `git diff --check`
- import-report dirty/untracked flags
- import-report verdict
- whether the report HEAD matches or is an ancestor of the current HEAD

## Verdicts

GREEN means the current lane matches the import report or is a clean descendant
of a GREEN import report.

YELLOW means the zip/report is missing, incomplete, unreadable, or the import
report itself needs review.

RED means current branch, status, diff check, or HEAD lineage conflicts with the
Deployment V2 report.

## Guardrail Confirmation

V1 remains `local_only`.

Hosted deployment remains blocked.

No deploy command, CI/CD workflow, container/image, public tunnel, secret,
credential, hosted routing, or production runtime path was created.
