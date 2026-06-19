# Deployment V2 D41 Local Operator Non-Invasive Checklist

## Scope

This checklist confirms local operator path documentation without touching the
Outcome repo or changing app/runtime behavior. It is documentation only. It
does not launch the app, approve hosted deployment, create deploy commands, add
CI/CD, create containers/images, expose public ports, create secrets, route
production traffic, or define hosted smoke plans.

## Current Operator Path

Normal operator path:

```text
C:\NWR\Niners-War-Room-outcome
```

Normal operator branch:

```text
main
```

Deployment V2 checkout:

```text
C:\NWR\Niners-War-Room-deploy-v2
```

The Deployment V2 checkout is discovery/docs/validation only. It is not the
normal operator app path.

## Non-Invasive Checks

Allowed read-only checks:

```powershell
git branch --show-current
git rev-parse HEAD
git status --short
```

These checks may be used to confirm documentation and branch state. They are
not app launch commands and are not deploy commands.

## Ownership Boundary

Any Outcome behavior question belongs to Outcome HQ, not Deployment V2.

Deployment V2 may document the operator path, but it must not change Outcome
runtime behavior, app behavior, generated Outcome artifacts, or the Outcome
worktree.

## Documentation Verdict Examples

GREEN:

- docs identify `C:\NWR\Niners-War-Room-outcome` as the normal operator path
- docs identify `main` as the normal operator branch
- docs say Deployment V2 is discovery/docs/validation only

YELLOW:

- older historical path references remain but a newer desktop-era correction is
  present
- path wording is incomplete but not contradictory

RED:

- docs present the Deployment V2 checkout as the normal app operator path
- docs imply hosted deployment approval exists
- docs instruct an app/runtime behavior change from Deployment V2

## Current Posture

V1 remains `local_only`.

Hosted deployment remains BLOCKED.

No deploy command, CI/CD workflow, container/image, public route, public tunnel,
hosted smoke plan, secret, credential, or production runtime path is approved.
