# Mock Draft Master Handoff Report

## Master Summary

- Lane: Mock Draft HQ.
- Repo: `C:\NWR\Niners-War-Room-mock-draft`.
- Branch: `work/mock-draft-simulator`.
- Latest committed baseline before closeout runway:
  `9d7f432fd9fbbe5711cfb6c878ba10a820b43861`.
- Expected final status after validation: clean.

## What Master Should Record

Mock Draft infrastructure is GREEN. Actual draft-use remains YELLOW/HOLD
because real inputs are not yet supplied or validated.

## Required Real Inputs

1. Frozen rookie input path.
2. Dropped/available veteran pool.
3. Final pick order.
4. NWR/my pick numbers.
5. Rosters/keepers.
6. Team needs/opponent tendencies.
7. NWR private value source.
8. ADP/market behavior source.

## Validation Status

State smoke, input readiness, real-input preflight, focused lane-local pytest,
and focused lane-local Ruff are the required handoff gates. Missing manifest or
missing real files remain YELLOW, not RED.

## Forbidden Actions

Do not run simulations, wire app UI, modify Rookie/Outcome/Drop Decision
work, create production rankings/sorting/probabilities/bands, or commit
`data/`, `local_exports/`, `.venv`, caches, logs, generated files, real inputs,
or local manifests.

## Next Approved Handoff

When Master can provide local-only real input paths, hand back to Mock Draft HQ
with a read-only real-input validation prompt. Do not approve simulation until
input readiness is GREEN.
