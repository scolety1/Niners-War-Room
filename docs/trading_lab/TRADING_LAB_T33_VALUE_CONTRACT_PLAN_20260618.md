# Trading Lab T33 Value Contract Plan - 2026-06-18

## Goal

Define pure in-memory fantasy trade value contracts before adding fixture-backed helpers.

## Scope

- Add dataclasses under `src/trading_lab/trade_value_contracts.py`.
- Keep NWR private value separate from public fantasy market value.
- Support fake players, picks, teams, package sides, scores, and manual reviews.

## Guardrails

- No file I/O.
- No real data loading.
- No imports from Outcome, Rookie, Mock Draft, Drop Decision, or Master lanes.
- No public fantasy source integration.
- No automated fantasy trade submission or automatic decisioning.

## Validation

- Dataclass instantiation tests.
- Value separation tests.
- Guardrail text checks.
