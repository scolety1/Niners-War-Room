# Trading Lab T57 Scenario Coverage Plan - 2026-06-18

## Goal

Expand fixture review scenarios to cover how the user will actually use Trade Lab.

## Scenarios

- Trade for elite player.
- Trade away aging veteran.
- Consolidate depth.
- Pick conversion.
- Drop pressure cleanup.
- Opponent-fit package.
- Market-fair but NWR-negative trap.
- NWR-positive but unrealistic trap.
- Keeper-damage trap.
- All assets untouchable fallback.

## Guardrails

- Fixture-only.
- No real integration.
- No generated outputs.
- No automated decisioning.

## Validation

Tests confirm each scenario exists, returns reviewable output, traps produce warnings, and fallback scenarios do not crash.
