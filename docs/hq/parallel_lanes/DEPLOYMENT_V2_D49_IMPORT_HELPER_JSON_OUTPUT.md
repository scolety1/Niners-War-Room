# Deployment V2 D49 Import Helper JSON Output

## Scope

This document records machine-readable JSON output for the read-only Deployment
V2 import report comparison helper. It does not approve hosted deployment,
create deploy commands, add CI/CD, create containers/images, expose public
ports, create secrets, route production traffic, create zip exports, or change
app/runtime behavior.

## Usage

Human output remains default:

```powershell
python scripts\compare_deployment_v2_import_report.py "<MASTER_IMPORT_ZIP>"
```

JSON output:

```powershell
python scripts\compare_deployment_v2_import_report.py "<MASTER_IMPORT_ZIP>" --json
```

## JSON Contents

The JSON output includes verdict, reasons, report HEAD, current HEAD,
ancestor-or-match status, clean status, and diff-check status.

Missing or invalid zip input returns non-GREEN JSON rather than crashing.

## Current Posture

V1 remains `local_only`.

Hosted deployment remains BLOCKED.
