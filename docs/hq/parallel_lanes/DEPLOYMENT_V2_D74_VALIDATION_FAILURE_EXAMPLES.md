# Deployment V2 D74 Validation Failure Examples

These examples show how to report validation failures safely. They are not instructions to deploy, host, route traffic, create credentials, add CI/CD, or create containers/images.

V1 remains `local_only`. Hosted deployment remains blocked. No deploy command exists. Deployment V2 is not the operator app path.

## Dirty Status

Verdict: RED

Report:

```text
git status --short returned tracked or untracked changes before work.
Stop and report the exact status lines.
```

## Guard Violation

Verdict: RED

Report:

```text
Local-only surface guard found a forbidden surface in an executable or command-oriented file.
Stop unless the fix is inside Deployment V2 docs/scripts/tests and does not weaken the guard.
```

## Docs Audit Failure

Verdict: RED

Report:

```text
Docs audit found missing local-only language or language implying hosted deployment readiness.
Fix only Deployment V2 docs language within allowed scope.
```

## Import Zip Missing

Verdict: YELLOW or SKIPPED

Report:

```text
Import report comparison was requested but the provided zip path was missing.
Do not create a zip export unless explicitly approved.
```

## Baseline Mismatch

Verdict: RED

Report:

```text
Current HEAD does not descend from the accepted baseline.
Stop and report current HEAD, baseline, and branch.
```

## Tests Unavailable

Verdict: YELLOW

Report:

```text
Python or pytest was unavailable. Continue docs-only work if allowed and report skipped script/test validation.
```

## Hosted Request Blocked

Verdict: BLOCKED

Report:

```text
Hosted deployment remains blocked pending hosted target, owner, secrets policy, data policy, access policy, rollback policy, deploy command policy, CI/CD policy, public/private routing policy, and hosted smoke plan.
```
