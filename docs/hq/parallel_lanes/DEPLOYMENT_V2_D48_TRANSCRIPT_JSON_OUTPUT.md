# Deployment V2 D48 Transcript JSON Output

## Scope

This document records optional JSON output for the read-only Deployment V2
operator transcript printer. It does not approve hosted deployment, create
deploy commands, add CI/CD, create containers/images, expose public ports,
create secrets, route production traffic, create zip exports, or change
app/runtime behavior.

## Usage

Human output remains the default:

```powershell
python scripts\print_deployment_v2_operator_transcript.py
```

JSON output:

```powershell
python scripts\print_deployment_v2_operator_transcript.py --json
```

Default behavior writes to stdout only. File output requires an explicit path
and is intended only for temp-file tests or separately approved use.

## JSON Contents

The JSON transcript includes branch, head, validation summary, docs consistency
summary, hosted blockers, and final verdict.

Hosted deployment remains BLOCKED.
