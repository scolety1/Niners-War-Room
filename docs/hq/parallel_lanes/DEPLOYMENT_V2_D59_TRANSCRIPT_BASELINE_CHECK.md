# Deployment V2 D59 Transcript Baseline Check

The operator transcript printer can include the optional readiness baseline ancestry result.

## Commands

Default transcript:

```powershell
python scripts/print_deployment_v2_operator_transcript.py
```

Baseline-enriched transcript:

```powershell
python scripts/print_deployment_v2_operator_transcript.py --baseline <accepted-baseline-commit>
```

JSON transcript:

```powershell
python scripts/print_deployment_v2_operator_transcript.py --baseline <accepted-baseline-commit> --json
```

The default still writes nothing and prints to stdout. An output file is used only when an operator explicitly supplies a path, typically inside a temporary test fixture.

This transcript is validation-only. It does not deploy, create deploy commands, expose public ports, create credentials, add CI/CD, create containers/images, or change app behavior.

V1 remains `local_only`. Hosted deployment remains blocked. No deploy command exists. Deployment V2 is not the operator app path.
