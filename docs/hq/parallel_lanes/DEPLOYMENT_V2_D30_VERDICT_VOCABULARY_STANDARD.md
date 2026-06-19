# Deployment V2 D30 Verdict Vocabulary Standard

## Scope

This standard defines Deployment V2 validation vocabulary for HQ reports. It is
documentation only. It does not approve hosted deployment, create deploy
commands, add CI/CD, create containers/images, expose public ports, create
secrets, route production traffic, or change app/runtime behavior.

## GREEN

Use GREEN when the requested local-only validation passed and no guardrail risk
was found.

For Deployment V2, GREEN means local discovery/readiness evidence is clean. It
does not mean hosted deployment is ready.

## YELLOW

Use YELLOW when the lane appears safe but evidence is incomplete or needs
review.

Examples:

- optional import report is unavailable
- validation environment is missing Python
- report bundle is incomplete
- current HEAD is newer than a report and lineage has not been checked
- baseline validation is partially blocked by known environment limits

## RED

Use RED when a hard guardrail is violated or a validation check finds a blocked
surface.

Examples:

- wrong branch
- dirty worktree before work
- deploy command surface detected
- CI/CD workflow detected
- container/image surface detected
- public tunnel or hosted routing surface detected
- secret/credential surface detected
- protected lane behavior touched
- generated/data/local-only artifacts staged or committed

## BLOCKED

Use BLOCKED when a category of work is not approved regardless of whether local
validation passes.

Hosted deployment remains BLOCKED until HQ approves:

- hosted target
- owner
- secrets policy
- data policy
- access policy
- rollback policy
- deploy command policy
- CI/CD policy
- public/private routing policy
- hosted smoke plan

Hosted deployment is BLOCKED, not merely YELLOW, until those approvals exist.

## SKIPPED

Use SKIPPED when an optional validation path was intentionally not run and its
absence is acceptable for the current task.

Example: import-report comparison is SKIPPED when no Master import zip is
provided and the task does not require one.

## PASS

Use PASS for an individual check that succeeded inside a larger GREEN/YELLOW/RED
report.

Example: `git diff --check` PASS means the command returned no output.

## FAIL

Use FAIL for an individual check that did not pass. Convert FAIL into the
appropriate overall verdict:

- FAIL on hard guardrails means RED
- FAIL because evidence is missing may mean YELLOW
- FAIL on optional checks may remain SKIPPED only when explicitly allowed

## Current Deployment V2 Posture

V1 remains `local_only`.

Local-only validation can be GREEN.

Hosted deployment remains BLOCKED.

No deploy command, CI/CD workflow, container/image, public route, public tunnel,
hosted smoke plan, secret, credential, or production runtime path is approved.
