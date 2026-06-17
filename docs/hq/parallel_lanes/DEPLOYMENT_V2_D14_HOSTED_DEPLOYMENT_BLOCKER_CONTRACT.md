# Deployment V2 D14 Hosted Deployment Blocker Contract

## Scope

This contract records the current hosted deployment blocker for Niners War Room
V1. It is documentation only. It does not approve hosted deployment, create a
deploy command, create secrets, expose public ports, edit app/source behavior,
change Outcome behavior, touch rookie files, merge to `main`, or push.

## Hosted Deployment Status

V1 hosted deployment is blocked.

The approved operating stance remains:

```text
local_only
```

The approved operator mode remains:

```text
manual_local_streamlit
```

## Deploy Command Status

No deploy command exists.

No deploy command may be created, documented, generated, tested, or run without
explicit HQ approval in a future hosted-deployment sprint.

The only supported operator command right now is local Streamlit:

```powershell
streamlit run app/main.py
```

That command starts a local app session. It is not a deployment command.

## Required Future Approvals Before Hosted Deployment

Before any hosted deployment work may begin, HQ must approve:

1. Hosting target.
2. Deployment owner.
3. Secrets and credential policy.
4. Data policy for data packs, local exports, PDFs, caches, logs, and generated
   artifacts.
5. Public/private access policy.
6. CI vs manual deployment policy.
7. Rollback policy.
8. Cost/risk acceptance.
9. Hosted smoke test plan.
10. Branch/release ownership and review rules.
11. Static guardrails proving local artifacts and secrets cannot be packaged or
    uploaded accidentally.

Without those approvals, hosted deployment work remains blocked.

## Allowed Now

Allowed now:

- manual local Streamlit operation
- local-only operator documentation
- local-only readiness/review docs
- local operator path and branch documentation
- local Rankings/Outcome label check guidance

Normal operator path:

```text
C:\Users\smcol\Documents\Vacation\Niners-War-Room-outcome
```

Normal operator branch:

```text
main
```

## Not Allowed Now

Not allowed now:

- deploy scripts
- deploy commands
- release scripts
- CI/CD deploy workflows
- platform manifests
- Streamlit Cloud configuration
- Procfiles
- containers/images
- release tags
- public port exposure
- public tunnels or hosted shares
- credentials or secrets
- hosted data upload
- merge to `main`
- push to `main`
- app/source behavior changes
- Outcome behavior/display-head/sorting/hidden-key/promoted-artifact changes
- rookie changes
- `data/`, `local_exports/`, or `.venv/` commits

## Outcome Numeric Columns And Hosting

Outcome Numeric Columns V1 is complete for local/main use.

That local readiness does not imply hosted deployment approval. The approved
Outcome heads remain:

- QB T12
- RB T12
- RB T24
- WR T12
- WR T24
- WR T36
- TE T12

Top 6 heads, unapproved heads, sorting/ranking effects, hidden sort keys, and
promoted artifacts remain blocked.

## Blocker-Contract Verdict

Verdict: `GREEN_FOR_HOSTED_DEPLOYMENT_BLOCKER_CONTRACT`

Reason:

- V1 hosted deployment is explicitly blocked.
- No deploy command exists.
- Future hosted approvals are enumerated.
- Local-only operation remains allowed.
- Hosted/deploy/platform/secrets/public-port paths remain blocked.
- Outcome local readiness is separated from hosting approval.

## Guardrail Confirmation

- No deploy command was created.
- No deploy, push, merge, or main push occurred.
- No secrets or credentials were created.
- No public ports were exposed.
- No app/source behavior was changed.
- No Outcome model behavior, displayed heads, sorting, hidden keys, or promoted
  artifacts were changed.
- No rookie files were touched.
- No `data/`, `local_exports/`, or `.venv/` files were staged or committed.
