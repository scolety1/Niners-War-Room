# Deployment V2 D23 Desktop Operator Path Reconciliation

## Scope

This is a docs-only reconciliation of the normal local operator app path after
desktop migration. It does not touch the Outcome repo, approve hosted
deployment, create deploy commands, add CI/CD, create containers/images, expose
public ports, create secrets, route production traffic, or change app/runtime
behavior.

## Current Desktop-Era Normal Operator Path

For desktop-era local V1 operation, the normal operator app path is:

```text
C:\NWR\Niners-War-Room-outcome
```

The normal operator branch is:

```text
main
```

This is the path an operator should use for normal local app operation after
desktop migration.

## Deployment V2 Checkout Is Not The Operator App Path

The Deployment V2 checkout is:

```text
C:\NWR\Niners-War-Room-deploy-v2
```

That checkout is for Deployment V2 discovery/docs/validation work only. It is
not the normal operator app folder.

## Legacy Path References

Several historical Deployment V2 docs still mention the earlier laptop-era or
pre-desktop path:

```text
C:\Users\smcol\Documents\Vacation\Niners-War-Room-outcome
```

Those references are historical context unless a newer desktop-era note says
otherwise. Do not use them as the current desktop operator path.

Search summary from D23:

- legacy path references found in historical Deployment V2 docs
- no Outcome repo files were opened or changed
- no historical docs were blindly rewritten
- this D23 note is the current desktop-era correction

## Current Posture

V1 remains `local_only`.

Hosted deployment remains blocked.

No deploy command exists.

No CI/CD workflow, container/image, hosted route, public tunnel, secret,
credential, hosted smoke plan, or production runtime path is approved.

## Future Agent Rule

When a future Deployment V2 task asks for the normal operator path, use:

```text
C:\NWR\Niners-War-Room-outcome
```

When a future task asks for the Deployment V2 working checkout, use:

```text
C:\NWR\Niners-War-Room-deploy-v2
```

Do not treat the Deployment V2 checkout as the normal local app operation path.
