# Deployment V2 D19 Local-Only Guard Report Mode

## Scope

This document records a read-only validation improvement for the Deployment V2
local-only surface guard. It does not approve hosted deployment, create deploy
commands, add CI/CD, create containers/images, expose public ports, create
secrets, alter app/runtime behavior, or change any other lane.

## Report Mode

The existing human-readable guard remains backward-compatible:

```powershell
python scripts\validate_local_only_surface_guard.py
```

The guard now also supports a machine-readable JSON report:

```powershell
python scripts\validate_local_only_surface_guard.py --report json
```

The report is validation-only. It is not a deploy plan, readiness approval, or
hosted smoke test.

## Stable Fields

The JSON report includes:

- `verdict`: `GREEN` when no blocked surfaces are detected, otherwise `RED`
- `root`: repository root scanned
- `checked_path_count`: number of repository files checked after local skip
  rules
- `checked_categories`: blocked path, manifest, command-surface, and pattern
  categories used by the guard
- `blocked_surface_count`: total blocked surfaces detected
- `reason_summary`: count of blocked findings by reason
- `violations`: blocked path and reason rows

## Current GREEN Expectation

For the current Deployment V2 lane, report mode should return:

```text
"verdict": "GREEN"
"blocked_surface_count": 0
"reason_summary": {}
"violations": []
```

## Guardrail Confirmation

V1 remains `local_only`.

Hosted deployment remains blocked.

No deploy command, CI/CD workflow, container/image, public tunnel, secret,
credential, hosted routing, or production runtime path was created.
