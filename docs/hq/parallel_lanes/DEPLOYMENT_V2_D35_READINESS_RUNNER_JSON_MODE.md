# Deployment V2 D35 Readiness Runner JSON Mode

## Scope

This document records a machine-readable JSON output mode for the read-only
Deployment V2 readiness runner. It does not approve hosted deployment, create
deploy commands, build, serve, expose public ports, create credentials, alter
data, add CI/CD, create containers/images, route production traffic, or change
app/runtime behavior.

## Runner Modes

Human-readable mode remains backward-compatible:

```powershell
python scripts\run_deployment_v2_readiness_checks.py
```

Machine-readable mode:

```powershell
python scripts\run_deployment_v2_readiness_checks.py --json
```

The older report flag also works:

```powershell
python scripts\run_deployment_v2_readiness_checks.py --report json
```

## JSON Fields

The JSON report includes:

- `verdict`
- `branch`
- `head`
- `clean_status`
- `diff_check`
- `local_only_guard`
- `guard_report`
- `import_report`
- `skipped_checks`
- `blockers`
- `violations`
- `checks`

When no import zip is supplied, `import_report` is `SKIPPED`. That is allowed
for local-only validation and is not a hosted deployment readiness claim.

## Current Posture

V1 remains `local_only`.

Hosted deployment remains BLOCKED.

No deploy command, CI/CD workflow, container/image, public route, public tunnel,
hosted smoke plan, secret, credential, or production runtime path is approved.
