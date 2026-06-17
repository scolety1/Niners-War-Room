# Deployment V2 Local-Only Operator Handoff Closeout

## Scope

This closeout summarizes the local-only operator readiness lane for Niners War
Room V1. It is a documentation handoff only. It does not approve hosted
deployment, create a deploy command, expose public ports, create secrets, or
change app/Outcome/Rookie behavior.

## Final V1 Mode

V1 mode remains:

```text
local_only
```

Official supported run mode:

```text
manual_local_streamlit
```

## Normal Operator Path And Branch

Normal operator path:

```text
C:\Users\smcol\Documents\Vacation\Niners-War-Room-outcome
```

Normal operator branch:

```text
main
```

The Deployment V2 worktree remains a planning/release-governance lane, not the
normal operator app folder.

## Official Local Run Command

Run from the normal operator path after the local environment is ready:

```powershell
streamlit run app/main.py
```

Open Rankings locally at:

```text
http://localhost:8501/rankings
```

If Streamlit chooses another local port, use the local port printed in the
terminal and append `/rankings`.

## Operator Docs

Use these docs for local-only operation:

- D3 runbook:
  `docs/hq/parallel_lanes/DEPLOYMENT_V2_LOCAL_STREAMLIT_OPERATOR_RUNBOOK.md`
- D5 quick-start:
  `docs/hq/parallel_lanes/DEPLOYMENT_V2_LOCAL_STREAMLIT_QUICK_START_CHECKLIST.md`
- D7 UI label guide:
  `docs/hq/parallel_lanes/DEPLOYMENT_V2_LOCAL_STREAMLIT_UI_LABEL_VISUAL_CHECK_GUIDE.md`
- D8 readiness re-audit:
  `docs/hq/parallel_lanes/DEPLOYMENT_V2_NON_TECHNICAL_OPERATOR_READINESS_REAUDIT.md`

## Outcome Numeric Columns Available Locally

Approved V1 Outcome heads for local operator checks:

- QB T12
- RB T12
- RB T24
- WR T12
- WR T24
- WR T36
- TE T12

Blocked display/output behavior:

- no Top 6 heads
- no unapproved heads
- no sorting/ranking effects
- no hidden sort keys
- no promoted artifacts

## Hosted Deployment Status

Hosted deployment remains blocked.

No hosted target, deployment owner, secrets policy, data policy, CI/manual
deployment policy, hosted rollback policy, deploy command, container, CI/CD
workflow, public port, or hosted release is approved.

## Deploy Command Status

No deploy command exists.

The only supported operator command is the local Streamlit command:

```powershell
streamlit run app/main.py
```

## What An Operator Can Safely Do Now

An operator can safely:

1. Use the selected normal operator path on `main`.
2. Create and activate a local `.venv`.
3. Install dependencies from `requirements.txt`.
4. Start the app locally with `streamlit run app/main.py`.
5. Open the local Rankings page.
6. Confirm approved Outcome labels.
7. Stop the local app with `Ctrl+C`.
8. Ask HQ if the local page, labels, path, or branch do not match the docs.

## What An Operator Must Not Do

An operator must not:

- deploy the app
- push or merge without HQ approval
- create a deploy command
- expose public ports
- create public tunnels or hosted shares
- create secrets or credentials
- create CI/CD deploy workflows
- create containers or images
- edit app behavior
- change Outcome model behavior, displayed heads, sorting, hidden keys, or
  promoted artifacts
- touch rookie files
- commit `.venv/`, `data/`, or `local_exports/`

## Required Approval Before Any Hosted Deployment Sprint

HQ must approve all of the following before any hosted deployment sprint:

1. Hosted stance and hosting target.
2. Deployment owner and release branch.
3. Access policy.
4. Secrets and credential policy.
5. Data upload, persistence, and logging policy.
6. Runtime live-API policy.
7. CI/manual deployment policy.
8. Rollback policy.
9. Static guardrails for excluding private local artifacts.
10. Human privacy review.

## Final Local-Only Operator Readiness Verdict

Verdict: `GREEN_FOR_LOCAL_ONLY_OPERATOR_HANDOFF`

Reason:

- The normal operator path is selected.
- The normal branch is selected.
- The local quick-start is documented.
- The local run command is documented.
- The Rankings URL and UI label checks are documented.
- The non-technical operator readiness re-audit is GREEN.
- Hosted deployment remains blocked.

Useful future polish remains optional: add screenshots if HQ wants a visual
handoff packet and update the D5 quick-start example path to the D6-selected
operator path.
