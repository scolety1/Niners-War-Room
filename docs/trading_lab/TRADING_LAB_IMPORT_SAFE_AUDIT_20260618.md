# Trading Lab Import-Safe Audit

Date: 2026-06-18

## Purpose

This audit records why the Trading Lab lane is safe to import or hand off as a
paper/research-only foundation.

## Allowed Historical Paths

- `docs/trading_lab/`
- `src/trading_lab/` for isolated validation-only helpers and constants.
- `tests/test_trading_lab_*.py` for focused validation-only tests.

## Prohibited Paths

The following paths must remain untouched and unstaged:

- `data/`
- `local_exports/`
- `.venv/`
- caches
- logs
- generated artifact folders
- `app/`
- deployment files
- fantasy-football lanes and behavior

## Generated Artifact Note

If inherited generated artifacts are discovered, they must remain untracked and
unstaged. T13 does not create generated outputs, market datasets, reports, or
simulation artifacts.

## Fantasy-Lane Confirmation

Trading Lab remains separate from Outcome, Rookie, Mock Draft, Drop Decision,
Deployment V2, and Master HQ behavior.

## Boundary

Docs may describe policy and process. Source code may only validate in-memory
paper/research payloads. Tests may only use fake inline payloads. No file I/O,
network, market-data fetching, broker/API integration, credentials, execution,
app wiring, deployment, or generated outputs are allowed.
