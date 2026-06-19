# Deployment V2 D71 Readiness All-Checks Mode

The readiness runner supports an optional all-checks mode for broader read-only validation.

## Commands

Normal readiness:

```powershell
python scripts/run_deployment_v2_readiness_checks.py
```

All available safe checks:

```powershell
python scripts/run_deployment_v2_readiness_checks.py --all
```

JSON output:

```powershell
python scripts/run_deployment_v2_readiness_checks.py --all --json
```

Optional enrichments:

```powershell
python scripts/run_deployment_v2_readiness_checks.py --all --baseline <accepted-baseline-commit>
python scripts/run_deployment_v2_readiness_checks.py --all --import-zip <master-import-zip>
```

## Behavior

`--all` keeps the normal readiness checks and adds safe schema smoke tests when those tests are present. Optional import and baseline checks remain `SKIPPED` unless their arguments are supplied.

This mode is validation-only. It does not deploy, serve, expose public ports, create credentials, add CI/CD, create containers/images, or change app behavior.

V1 remains `local_only`. Hosted deployment remains blocked. No deploy command exists. Deployment V2 is not the operator app path.
