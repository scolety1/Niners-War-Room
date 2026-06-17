# Deployment V2 D13 Local-Only Operator Handoff Index

## Purpose

This index gives HQ and a local operator a single reading order for the Niners
War Room V1 local-only operator docs. It is documentation only. It does not
approve hosted deployment, create a deploy command, expose public ports, create
secrets, edit app/source behavior, change Outcome behavior, touch rookie files,
merge to `main`, or push.

## Normal Operator Setup

Normal operator path:

```text
C:\Users\smcol\Documents\Vacation\Niners-War-Room-outcome
```

Normal operator branch:

```text
main
```

V1 status:

```text
local_only
```

Hosted deployment status:

```text
blocked
```

## Recommended Reading Order

1. Quick-start checklist:
   `docs/hq/parallel_lanes/DEPLOYMENT_V2_LOCAL_STREAMLIT_QUICK_START_CHECKLIST.md`

   Use this first when the operator just needs to start the local app.

2. Full operator runbook:
   `docs/hq/parallel_lanes/DEPLOYMENT_V2_LOCAL_STREAMLIT_OPERATOR_RUNBOOK.md`

   Use this for environment policy, preflight, smoke checks, troubleshooting,
   stop/restart, and local rollback guidance.

3. UI label visual check guide:
   `docs/hq/parallel_lanes/DEPLOYMENT_V2_LOCAL_STREAMLIT_UI_LABEL_VISUAL_CHECK_GUIDE.md`

   Use this to check Rankings labels and Outcome columns without changing the
   app.

4. Operator readiness review:
   `docs/hq/parallel_lanes/DEPLOYMENT_V2_LOCAL_ONLY_RELEASE_OPERATOR_READINESS_REVIEW.md`

   Use this for the original D4 readiness findings and why later quick-start
   and label docs were needed.

5. Normal operator path selection:
   `docs/hq/parallel_lanes/DEPLOYMENT_V2_NORMAL_LOCAL_OPERATOR_PATH_SELECTION.md`

   Use this for why normal operation should use the Outcome/main worktree.

6. Local-only operator handoff closeout:
   `docs/hq/parallel_lanes/DEPLOYMENT_V2_LOCAL_ONLY_OPERATOR_HANDOFF_CLOSEOUT.md`

   Use this for the local-only handoff summary.

7. Review hold and path polish docs:
   `docs/hq/parallel_lanes/DEPLOYMENT_V2_LOCAL_ONLY_BRANCH_REVIEW_AND_PUSH_HOLD.md`
   and
   `docs/hq/parallel_lanes/DEPLOYMENT_V2_D12_DOCUMENTATION_CONSISTENCY_RECONCILIATION.md`

   Use these for branch review readiness and the final documentation
   consistency record.

## Exact Local Command

Run from the normal operator path:

```powershell
streamlit run app/main.py
```

This is the supported local Streamlit command. It is not a deploy command.

## Expected Rankings Path

Open Rankings locally at:

```text
/rankings
```

Typical local URL:

```text
http://localhost:8501/rankings
```

If Streamlit prints a different local port, use that local port and append
`/rankings`.

## Approved Outcome Heads

Approved V1 Outcome heads:

- QB T12
- RB T12
- RB T24
- WR T12
- WR T24
- WR T36
- TE T12

## Blocked Items

The following remain blocked:

- hosted deployment
- deploy commands
- public ports
- public tunnels or hosted shares
- secrets or credentials
- Top 6 heads
- unapproved Outcome heads
- sorting/ranking effects from Outcome columns
- hidden sort keys
- promoted artifacts
- `data/`, `local_exports/`, or `.venv/` commits
- app/source behavior changes
- Outcome behavior/display-head/sorting/hidden-key/promoted-artifact changes
- rookie changes
- merge to `main`
- push to `main`

## If The App Does Not Start

If the app does not start:

1. Confirm PowerShell is in the normal operator path.
2. Confirm the branch is `main`.
3. Confirm `.venv` is active.
4. Reinstall documented dependencies from `requirements.txt` if needed.
5. Retry `streamlit run app/main.py`.
6. If Streamlit shows a traceback or Rankings does not load, stop and ask HQ.

Do not repair startup problems by creating deploy commands, exposing public
ports, changing app behavior, changing Outcome behavior, editing rookie files,
or committing local artifacts.

## Handoff Verdict

Verdict: `GREEN_FOR_LOCAL_ONLY_OPERATOR_HANDOFF_INDEX`

The local-only operator docs now have a clear reading order, selected path,
selected branch, local command, Rankings path, approved Outcome labels, blocked
items, and stop/ask-HQ guidance.
