# Mock Draft Draft-Day Safety Runbook

## Pre-Run Checks

- Confirm branch `work/mock-draft-simulator`.
- Confirm clean git status.
- Run input readiness check.
- Run state smoke.
- Run pytest/Ruff through locked or approved ephemeral validation.

## Commands

```powershell
$uv = "C:\Users\codex-agent\.local\bin\uv.exe"
$env:PYTHONDONTWRITEBYTECODE="1"
& $uv run --locked python -B scripts/mock_draft_input_readiness_check.py
& $uv run --locked python -B scripts/mock_draft_state_smoke.py
```

## No-Simulation Gate

Do not run any mock draft until real inputs are present, schema-valid, and
source-separated. Missing inputs are YELLOW. Schema violations are RED.

## ADP / Market Checklist

- ADP/market supports opponent behavior, availability, and likely pick timing.
- ADP/market never becomes NWR private quality/value.
- Market context and NWR private values remain separate files/roles.

## Manual Review

- If a player is missing, stop and update local inputs after human review.
- If roster/keeper conflict appears, stop and reconcile local roster source.
- If pick order changes, revalidate pick order and my-pick subset.

## Stop Conditions

Stop for source contamination, app wiring, production rankings/sorting,
probability/band output, promoted artifacts, Rookie/Outcome modifications, or
any write into real input/export locations.

## Current Tooling

- Readiness renderer: stdout-only preflight report.
- Schema diagnostics: header comparison and contamination detection.
- Header aliases: safe identity aliases with manual review for ambiguous names.
- Adversarial fixtures: fake malformed inputs for contract tests.

Real draft simulation remains disallowed until real inputs validate GREEN.
