# Deployment V2 D22 Readiness Automation Bridge

## Scope

This bridge ties the D18 branch-readiness checklist, D19 guard report mode, and
D21 import-report comparison helper into one repeatable Deployment V2
GREEN/YELLOW/RED process.

It does not approve hosted deployment, create deploy commands, add CI/CD,
create containers/images, expose public ports, create secrets, route production
traffic, or change app/runtime behavior. Hosted deployment remains blocked.

## Required Process Before GREEN

Run the checks in this order.

### 1. Branch And HEAD

```powershell
git branch --show-current
git rev-parse HEAD
git rev-parse --short HEAD
git log -1 --pretty=%s
```

GREEN requires branch `work/deployment-v2-discovery` and an expected HEAD or a
clean descendant of the accepted baseline/import report.

### 2. Clean Worktree

```powershell
git status --short
```

GREEN requires no output.

### 3. Diff Check

```powershell
git diff --check
```

GREEN requires no output.

### 4. Local-Only Guard

Human-readable mode:

```powershell
python scripts\validate_local_only_surface_guard.py
```

Machine-readable mode:

```powershell
python scripts\validate_local_only_surface_guard.py --report json
```

GREEN requires:

```text
verdict: GREEN
blocked_surface_count: 0
violations: []
```

### 5. Master Import-Report Comparison

When a Master import verification bundle is provided, run:

```powershell
python scripts\compare_deployment_v2_import_report.py "<MASTER_IMPORT_ZIP_PATH>"
```

GREEN requires either an exact report HEAD match or a clean descendant of a
GREEN Deployment V2 report.

## GREEN Meaning

GREEN means the Deployment V2 discovery lane is clean, local-only guardrails
hold, and import lineage is explainable.

GREEN does not mean hosted deployment is ready.

GREEN does not approve CI/CD, containers/images, deploy commands, secrets,
public ports, hosted routing, production runtime behavior, or app UI wiring.

## YELLOW Meaning

Use YELLOW when the lane is probably safe but needs review:

- missing or unreadable import report bundle
- guard unavailable because Python is unavailable
- current HEAD is newer than the report but lineage has not been checked
- baseline validation is partially blocked by environment limits
- clean worktree but incomplete evidence for a GREEN claim

## RED Meaning

Use RED and stop when any hard guardrail is violated:

- wrong branch
- dirty worktree before work
- diff-check output before GREEN claim
- local-only guard detects blocked surfaces
- import report conflicts with current branch or HEAD lineage
- deploy command, CI/CD workflow, container/image, public route, tunnel, secret,
  credential, hosted smoke plan, or production runtime path appears
- another lane's behavior or protected paths are touched

## Final Readiness Packet

Every future Deployment V2 readiness packet should include:

- branch
- full HEAD
- short HEAD
- subject
- status result
- diff-check result
- local-only guard text result
- local-only guard report summary
- import-report comparison result, when applicable
- explicit statement that V1 remains `local_only`
- explicit statement that hosted deployment remains blocked
- GREEN/YELLOW/RED verdict
