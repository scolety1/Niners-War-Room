# Deployment V2 D29 Import Helper Edge-Case Hardening

## Scope

This document records edge-case coverage for the read-only Deployment V2 import
report comparison helper. It does not approve hosted deployment, create deploy
commands, add CI/CD, create containers/images, expose public ports, create
secrets, route production traffic, or change app/runtime behavior.

## Covered Edge Cases

The import helper now has focused coverage for:

- missing zip path
- invalid zip file
- zip without `05_DEPLOYMENT_V2.md`
- Deployment V2 report present but missing the full HEAD field
- report HEAD not matching or descending into current HEAD
- dirty current checkout

## Expected Verdict Behavior

Missing, invalid, or incomplete import reports return YELLOW because the lane
may still be safe but the import evidence is incomplete.

Current-state conflicts return RED because the lane cannot claim readiness when
branch, status, diff check, or HEAD lineage is unsafe.

## Guardrail Confirmation

The helper remains read-only. It reads the zip in memory and does not extract
source, data, exports, archives, or generated artifacts.

V1 remains `local_only`.

Hosted deployment remains blocked.

No deploy command, CI/CD workflow, container/image, public tunnel, hosted smoke
plan, secret, credential, hosted routing, or production runtime path was added.
