# Deployment V2 D37 Docs Consistency Audit

## Scope

This document records a read-only docs consistency audit helper for Deployment
V2. It does not rewrite docs, scan other lane worktrees, approve hosted
deployment, create deploy commands, add CI/CD, create containers/images, expose
public ports, create secrets, route production traffic, or change app/runtime
behavior.

## Helper

Run from the Deployment V2 checkout:

```powershell
python scripts\audit_deployment_v2_docs_consistency.py
```

Machine-readable validation output:

```powershell
python scripts\audit_deployment_v2_docs_consistency.py --json
```

The helper scans Deployment V2 docs under:

```text
docs/hq/parallel_lanes
```

## Required Consistency Points

The audit checks that docs still state:

- V1 remains `local_only`
- hosted deployment remains blocked
- no deploy command should be invented
- normal operator app path is `C:\NWR\Niners-War-Room-outcome`
- normal operator branch is `main`
- Deployment V2 checkout is not the operator app path

Legacy references to:

```text
C:\Users\smcol\Documents\Vacation\Niners-War-Room-outcome
```

are reported as notes when newer desktop-era documentation marks them as
historical.

## Current Posture

V1 remains `local_only`.

Hosted deployment remains BLOCKED.

No deploy command, CI/CD workflow, container/image, public route, public tunnel,
hosted smoke plan, secret, credential, or production runtime path is approved.
