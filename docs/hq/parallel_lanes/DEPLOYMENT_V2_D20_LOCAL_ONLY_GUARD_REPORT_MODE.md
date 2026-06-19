# Deployment V2 D20 Local-Only Guard Report Mode Operator Examples

## Scope

This is an operator-facing validation note for the Deployment V2 local-only
surface guard. It does not approve hosted deployment, create deploy commands,
add CI/CD, create containers/images, expose public ports, create secrets, route
production traffic, or change app/runtime behavior.

Report mode is for discovery validation only. It is not deployment readiness.

## Human-Readable Guard Mode

Use human-readable mode when a person is checking the lane manually:

```powershell
python scripts\validate_local_only_surface_guard.py
```

Expected GREEN output:

```text
Deployment V2 local-only surface guard passed: no deploy surfaces detected.
```

Any failure is at least YELLOW until the finding is reviewed. If the finding is
a real hosted/deploy surface, the verdict is RED.

## Machine-Readable Guard Mode

Use machine-readable mode when a report needs stable fields for an audit,
handoff, or branch-readiness comparison:

```powershell
python scripts\validate_local_only_surface_guard.py --report json
```

Expected GREEN output shape:

```json
{
  "blocked_surface_count": 0,
  "reason_summary": {},
  "verdict": "GREEN",
  "violations": []
}
```

The full report also includes the scanned root, checked path count, and checked
surface categories.

## Inert RED Example Shapes

The examples below describe report shapes only. They are not commands and are
not files to add to the repository.

Container/platform surface example:

```json
{
  "blocked_surface_count": 1,
  "reason_summary": {
    "hosted/container/platform manifest is present": 1
  },
  "verdict": "RED",
  "violations": [
    {
      "path": "INERT_EXAMPLE_CONTAINER_MANIFEST",
      "reason": "hosted/container/platform manifest is present"
    }
  ]
}
```

CI/CD workflow surface example:

```json
{
  "blocked_surface_count": 1,
  "reason_summary": {
    "CI/CD workflow file is present": 1
  },
  "verdict": "RED",
  "violations": [
    {
      "path": "INERT_EXAMPLE_CI_WORKFLOW",
      "reason": "CI/CD workflow file is present"
    }
  ]
}
```

## Operator Interpretation

GREEN means no blocked deploy surfaces were detected by this guard.

YELLOW means the guard could not run, the output was incomplete, or the result
needs lane-owner interpretation.

RED means a blocked deploy surface was detected and the agent must stop before
any further Deployment V2 work.

## Required Pairing

The guard report is not enough by itself for a Deployment V2 GREEN claim. It
must be paired with:

- correct branch
- expected HEAD/history
- clean `git status --short`
- clean `git diff --check`
- Master import-report comparison when a report bundle is provided
- confirmation that V1 remains `local_only`
- confirmation that hosted deployment remains blocked
