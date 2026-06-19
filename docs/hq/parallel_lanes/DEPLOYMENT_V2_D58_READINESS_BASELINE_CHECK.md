# Deployment V2 D58 Readiness Baseline Check

The read-only readiness runner can optionally verify that current HEAD descends from an accepted baseline commit.

## Commands

Default readiness does not require a baseline:

```powershell
python scripts/run_deployment_v2_readiness_checks.py
```

Baseline-enriched readiness:

```powershell
python scripts/run_deployment_v2_readiness_checks.py --baseline <accepted-baseline-commit>
```

JSON output:

```powershell
python scripts/run_deployment_v2_readiness_checks.py --baseline <accepted-baseline-commit> --json
```

## Behavior

- If no baseline is supplied, `baseline_ancestry` is `SKIPPED`.
- If a baseline is supplied and HEAD descends from it with clean status, `baseline_ancestry` is `GREEN`.
- If the baseline cannot be resolved, the result is non-GREEN and the reason is reported.
- If HEAD does not descend from the baseline, the result is `RED`.

This check is validation-only and uses local read-only git commands. It does not deploy, create deploy commands, expose public ports, create credentials, add CI/CD, create containers/images, or change app behavior.

V1 remains `local_only`. Hosted deployment remains blocked. No deploy command exists. Deployment V2 is not the operator app path.
