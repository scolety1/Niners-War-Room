# Mock Draft Draft-Day Operator Checklist

## Open And Verify

1. Open `C:\NWR\Niners-War-Room-mock-draft`.
2. Confirm branch `work/mock-draft-simulator`.
3. Confirm expected HEAD and clean `git status --short`.
4. Confirm `uv.lock`, `.venv`, `data`, and `local_exports` are not staged.

## Readiness

1. Run `scripts/mock_draft_input_readiness_check.py`.
2. Confirm fixture readiness is GREEN.
3. Confirm real readiness is GREEN before any draft-room use.
4. If real readiness is YELLOW, pause and collect missing inputs.
5. If schema readiness is RED, stop and repair the input contract.

## Manifest

- Real manifests belong in ignored local-only paths.
- Real manifests may point to local CSV files.
- Real manifests must not be committed.
- Market behavior and NWR private value must use separate roles.

## Manual Pause Points

- Frozen rookie input missing.
- Veteran pool missing or stale.
- Pick order changes.
- Roster/keeper conflict appears.
- Team-needs notes are missing.
- ADP/market separation cannot be confirmed.

## Report Back

Send branch, HEAD, status, readiness color, missing inputs, schema violations,
validation command results, and confirmation that no simulations ran.

## Fixture Operator Practice Gate

Before real inputs arrive, operators may rehearse only with the fixture practice
script. Confirm that `demo`, `status`, `available`, and `validate` run with
fixture-only and no-real-simulation language. This does not clear the real
draft-use HOLD; live mode still requires a GREEN real manifest and owner-approved
inputs.
