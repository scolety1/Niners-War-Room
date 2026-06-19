# Deployment V2 D53 Docs Audit JSON Output

Deployment V2 docs consistency audit supports human output by default and JSON output when an operator needs a stable validation report.

## Command

```powershell
python scripts/audit_deployment_v2_docs_consistency.py --json
```

This command is validation-only. It does not deploy, serve, route, create credentials, create containers, add CI/CD, or change app behavior.

## JSON Fields

The JSON report includes:

- `verdict`: `GREEN`, `YELLOW`, or `RED`.
- `required_phrases`: required local-only, hosted-blocked, no-deploy-command, operator-path, branch, and checkout-purpose language.
- `missing_phrases`: required language that is absent.
- `notes`: non-blocking notes, including historical-path notes.
- `blocked_language_hits`: docs language that incorrectly implies hosted deployment readiness.
- `historical_path_notes`: legacy Vacation-path references that are acceptable only as history.
- `findings`: complete audit finding list.

## GREEN Meaning

`GREEN` means Deployment V2 docs are internally consistent with the local-only discovery posture. It does not mean hosted deployment is ready.

Hosted deployment remains blocked until hosted target, owner, secrets policy, data policy, access policy, rollback policy, deploy command policy, CI/CD policy, public/private routing policy, and hosted smoke plan are explicitly approved.
