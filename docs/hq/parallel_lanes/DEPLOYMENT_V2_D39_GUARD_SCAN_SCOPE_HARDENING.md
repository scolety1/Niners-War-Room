# Deployment V2 D39 Guard Scan Scope Hardening

## Scope

This document records scan-scope clarification for the Deployment V2 local-only
surface guard. It does not approve hosted deployment, create deploy commands,
add CI/CD, create containers/images, expose public ports, create secrets, route
production traffic, define hosted smoke plans, or change app/runtime behavior.

## Root Selection

The guard still scans the current repository root by default:

```powershell
python scripts\validate_local_only_surface_guard.py
```

For safe temp-fixture validation, callers may provide an explicit root:

```powershell
python scripts\validate_local_only_surface_guard.py --root "<TEMP_FIXTURE_PATH>"
```

The positional root argument remains supported for backward compatibility.

## Default Scope

The guard excludes local-only and generated folders such as `.git`, `.venv`,
caches, `data`, `local_exports`, build output, and dependency folders.

The guard does not scan unrelated worktrees by default. It scans only the root
selected by the current working directory, positional root, or `--root`.

## Current Posture

V1 remains `local_only`.

Hosted deployment remains BLOCKED.

No deploy command, CI/CD workflow, container/image, public route, public tunnel,
hosted smoke plan, secret, credential, or production runtime path is approved.
