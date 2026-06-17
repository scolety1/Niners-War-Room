# Deployment V2 Normal Local Operator Path Selection

## Scope

This is a docs/review-only recommendation for the normal local operator path
for Niners War Room V1. It does not approve hosted deployment, create a deploy
command, create secrets, expose public ports, change app behavior, or alter
Outcome/Rookie/model artifacts.

## Current Evidence

Recent Deployment V2 work established:

- V1 remains `local_only`.
- The official supported run mode is `manual_local_streamlit`.
- The official local command is:

  ```powershell
  streamlit run app/main.py
  ```

- Hosted deployment remains blocked.
- The D5 quick-start still had one open operator-path gap because HQ had not
  selected the normal long-term folder for local operation.

The current worktree list shows:

| Path | Branch | Role |
|---|---|---|
| `C:\Users\smcol\Documents\Vacation\Niners-War-Room` | `work/hq-parallel-control` | HQ / Master Control |
| `C:\Users\smcol\Documents\Vacation\Niners-War-Room-outcome` | `main` | Main application worktree after Outcome V1 merge |
| `C:\Users\smcol\Documents\Vacation\Niners-War-Room-deploy-v2` | `work/deployment-v2-discovery` | Deployment planning and release governance |
| `C:\Users\smcol\Documents\Vacation\Niners-War-Room-rookies` | `work/rookie-framework-path` | Rookie lane |
| `C:\Users\smcol\Documents\Vacation\Niners-War-Room-drop-decision` | `work/drop-decision-day-review` | Drop Decision review lane |
| `C:\Users\smcol\Documents\Vacation\Niners-War-Room-mock-draft` | `work/mock-draft-simulator` | Mock Draft lane |
| `C:\Users\smcol\Documents\Vacation\Niners-War-Room-qa-data` | `work/data-test-hygiene` | QA / Data Hygiene lane |

## Recommended Normal Operator Path

Recommended normal operator path for V1 local use:

```text
C:\Users\smcol\Documents\Vacation\Niners-War-Room-outcome
```

Recommended normal operator branch:

```text
main
```

Reason:

- Outcome Numeric Columns V1 has already merged to `main`.
- The `Niners-War-Room-outcome` worktree is the current `main` application
  worktree.
- Normal operation should happen from the release/main application line, not
  from a planning branch.
- This keeps HQ, Rookie, Drop Decision, Mock Draft, QA/Data Hygiene, and
  Deployment V2 lanes isolated from routine local app operation.

## Deployment V2 Worktree Use

The Deployment V2 worktree should remain a planning/release-governance lane.

It should not be the normal operator app folder because it is on:

```text
work/deployment-v2-discovery
```

That branch is for deployment policy, runbook, path-selection, and readiness
documents. It is not the long-term local app surface for a non-technical
operator.

## Branch Selection

Normal local operation should use:

```text
main
```

`main` is the appropriate operator branch after Outcome V1 merged because it is
the release line carrying the accepted local-ready app state. Feature, review,
HQ, Rookie, Drop Decision, Mock Draft, QA, and Deployment V2 branches should
remain lane-specific unless HQ explicitly promotes their work.

## Quick-Start Checklist Relationship

The D5 quick-start checklist should be updated in a later docs-only sprint to
replace the pending path language with:

```powershell
Set-Location "C:\Users\smcol\Documents\Vacation\Niners-War-Room-outcome"
```

The rest of the checklist can continue to use:

```powershell
streamlit run app/main.py
```

This D6 review selects the recommended path only. It does not edit the D5
quick-start checklist.

## Still Blocked

The following remain blocked:

- hosted deployment
- deploy commands
- public ports
- public tunnels or hosted shares
- secrets or credential creation
- CI/CD deploy workflows
- containers or images
- `data/`, `local_exports/`, or `.venv/` commits
- app behavior changes
- Outcome model behavior changes
- Outcome displayed-head changes
- Outcome sorting, hidden-key, or promoted-artifact changes
- rookie changes

## HQ Decisions Remaining

HQ still needs to decide:

1. Whether to accept `C:\Users\smcol\Documents\Vacation\Niners-War-Room-outcome`
   on `main` as the official normal local operator path.
2. Whether to run a follow-up docs-only sprint to update the D5 quick-start with
   that selected path.
3. Whether screenshots or exact UI labels are needed for a non-technical
   operator handoff.

No hosted deployment decision is ready.

## Recommendation Verdict

Verdict: `GREEN_FOR_LOCAL_OPERATOR_PATH_SELECTION`

Recommended:

- Use `C:\Users\smcol\Documents\Vacation\Niners-War-Room-outcome`.
- Use branch `main`.
- Keep `C:\Users\smcol\Documents\Vacation\Niners-War-Room-deploy-v2` as
  planning/release-governance only.
- Keep V1 `local_only`.
- Keep hosted deployment blocked.

This resolves the operator-path selection gap for technical/local operation.
The remaining non-technical handoff gap is screenshots or exact UI labels.
