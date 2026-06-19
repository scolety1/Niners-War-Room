# Deployment V2 D27 Read-Only Readiness Runner

## Scope

This document records a read-only readiness runner for Deployment V2 discovery
validation. It does not deploy, build, serve, expose ports, create credentials,
alter data, add CI/CD, create containers/images, route production traffic, or
change app/runtime behavior.

## Runner

Run from the Deployment V2 checkout:

```powershell
python scripts\run_deployment_v2_readiness_checks.py
```

The runner performs:

- current branch check
- current HEAD check
- `git status --short`
- `git diff --check`
- local-only surface guard normal mode
- local-only surface guard report mode
- optional Master import-report comparison when `--import-zip` is supplied

If no import zip is supplied, import comparison is reported as `SKIPPED`; that
does not make the local checks fail.

## Optional Import Zip

When a Master import verification bundle is available:

```powershell
python scripts\run_deployment_v2_readiness_checks.py --import-zip "<MASTER_IMPORT_ZIP_PATH>"
```

The runner delegates import comparison to the existing read-only import helper.
It does not extract source, data, exports, archives, or generated artifacts.

## Optional JSON Report

For machine-readable validation output:

```powershell
python scripts\run_deployment_v2_readiness_checks.py --report json
```

JSON output is a validation report only. It is not hosted deployment readiness.

## Current Posture

V1 remains `local_only`.

Hosted deployment remains blocked.

No deploy command exists.

No CI/CD workflow, container/image, hosted route, public tunnel, hosted smoke
plan, secret, credential, or production runtime path is approved.
