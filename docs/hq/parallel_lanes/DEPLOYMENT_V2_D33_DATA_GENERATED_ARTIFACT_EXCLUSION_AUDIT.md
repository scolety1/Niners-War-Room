# Deployment V2 D33 Data Generated Artifact Exclusion Audit

## Scope

This guide explains how Deployment V2 avoids committing generated, data,
local-only, cache, log, archive, or secret artifacts. It is documentation only.
It does not clean artifacts, touch the Outcome repo, alter generated Outcome
artifacts, approve hosted deployment, create deploy commands, add CI/CD, create
containers/images, expose public ports, create secrets, route production
traffic, or change app/runtime behavior.

## Blocked Paths And Patterns

Deployment V2 agents must not stage or commit:

- `data/`
- `local_exports/`
- `.venv/`
- `.env`
- caches
- logs
- generated artifacts
- archives
- secrets
- credentials
- private keys
- service account files
- local-only data packs
- exported reports or packets

If any blocked path appears in `git status --short`, stop and review before
continuing.

## Required Audit Commands

Before any Deployment V2 commit, run:

```powershell
git status --short
git diff --check
```

For final readiness, also run:

```powershell
python scripts\validate_local_only_surface_guard.py
python scripts\run_deployment_v2_readiness_checks.py
```

These commands are validation-only. They are not deploy commands.

## Existing Tracked Generated Artifacts

If a future audit discovers an existing tracked generated artifact, report it as
an outside-lane note unless the user explicitly approves a cleanup lane.

Do not clean, rewrite, remove, or modify tracked generated artifacts from
Deployment V2 unless that exact cleanup is approved.

Do not touch the Outcome repo or generated Outcome artifacts from this lane.

## Commit Hygiene

Deployment V2 commits should be limited to:

- Deployment V2 docs under `docs/hq/parallel_lanes/`
- read-only validation scripts under `scripts/`
- matching focused tests under `tests/`

No app behavior, runtime behavior, data behavior, or hosted behavior should be
changed by Deployment V2 discovery work.

## Current Posture

V1 remains `local_only`.

Hosted deployment remains BLOCKED.

No deploy command, CI/CD workflow, container/image, public route, public tunnel,
hosted smoke plan, secret, credential, generated/data artifact, or production
runtime path is approved.
