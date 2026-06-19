# Deployment V2 D18 Branch Readiness Checklist

## Scope

This checklist is documentation only. It does not approve hosted deployment,
create deploy commands, add CI/CD, create containers/images, expose public
ports, create secrets or credentials, wire app UI, alter production runtime
behavior, or change Outcome behavior or any other lane.

Deployment V2 remains a discovery/docs/validation lane unless HQ explicitly
approves a future hosted-deployment sprint.

## Required Before Any GREEN Claim

Before any future Deployment V2 GREEN readiness claim, the agent must complete
and report every item below.

### 1. Branch Check

Run:

```powershell
git branch --show-current
```

Expected branch:

```text
work/deployment-v2-discovery
```

Any other branch is YELLOW until reconciled.

### 2. HEAD Check

Run:

```powershell
git rev-parse HEAD
git rev-parse --short HEAD
git log -1 --pretty=%s
```

Report the full hash, short hash, and commit subject. If the current HEAD is
newer than a migration/import baseline, explain why that branch movement is
expected and remote-backed or stop at YELLOW.

### 3. Status Check

Run:

```powershell
git status --short
```

Expected output:

```text

```

Any dirty, untracked, staged, or unstaged file is YELLOW until reviewed. Do not
claim GREEN with pending changes unless the task explicitly asked for an
in-progress working tree report.

### 4. Diff Check

Run:

```powershell
git diff --check
```

Expected output:

```text

```

Any whitespace or patch-format warning is YELLOW until fixed or explicitly
accepted by HQ.

### 5. Local-Only Surface Guard

If available, run:

```powershell
python scripts\validate_local_only_surface_guard.py
```

Expected result:

```text
Deployment V2 local-only surface guard passed: no deploy surfaces detected.
```

If `python` is not available on PATH, use the approved bundled Python runtime
for the Codex desktop session. If the guard cannot run, mark the claim YELLOW
and explain the limitation.

### 6. Master Import-Report Comparison

When a Master import verification bundle is provided, read the Deployment V2
report in the bundle and compare it to current lane state.

Required comparison fields:

- repo path
- expected branch
- current branch
- HEAD full hash
- HEAD short hash
- commit subject
- dirty/untracked status
- diff-check result
- remote branch ref, when included
- import verdict

If the current lane has moved beyond the report, explain the newer commit and
confirm it is expected branch movement. If the report says GREEN and current
state still matches or has expected clean branch movement, the import check can
remain GREEN. If the report conflicts with current state, mark YELLOW or RED
depending on severity.

## GREEN Standard

Deployment V2 may be reported GREEN only when all of the following are true:

- branch is `work/deployment-v2-discovery`
- status is clean
- diff check passes
- local-only guard passes, when available
- Master import-report comparison passes, when a report is provided
- V1 remains `local_only`
- hosted deployment remains blocked unless explicitly approved
- no deploy command surface exists
- no CI/CD, container, hosted routing, public tunnel, secret, or credential
  surface has been added
- no protected lane behavior or files were touched

## YELLOW Standard

Use YELLOW when the lane appears safe but needs review, such as:

- current HEAD is clean but newer than a provided import report and not yet
  explained
- the local-only guard cannot run because the environment is missing Python
- a report bundle is missing, unreadable, or does not contain Deployment V2
  details
- a dirty status exists only because of clearly unrelated local files that must
  be resolved before further work
- validation is partially blocked by baseline environment issues

## RED Standard

Use RED when any deploy or cross-lane risk is detected, including:

- deploy command, hosted platform config, CI/CD workflow, container/image,
  public tunnel, secret, credential, or production routing surface introduced
- V1 local-only posture weakened without explicit HQ approval
- Outcome, Rookie, Mock Draft, Drop Decision, Trading Lab, QA/Data Hygiene, or
  Master lane behavior changed from Deployment V2
- `data/`, `local_exports/`, `.env`, `.venv`, caches, logs, generated
  artifacts, or archives are staged or committed without explicit approval

## Final Report Template

Use this format for future Deployment V2 readiness reports:

```text
LANE: Deployment V2
REPO:
BRANCH:
HEAD:
STATUS:
DIFF CHECK:
LOCAL-ONLY GUARD:
MASTER IMPORT REPORT CHECK:
CURRENT PURPOSE:
CURRENTLY READY:
NOT READY / NEEDS REVIEW:
BLOCKERS:
CROSS-LANE CONTAMINATION RISK:
FINAL VERDICT: GREEN / YELLOW / RED
```
