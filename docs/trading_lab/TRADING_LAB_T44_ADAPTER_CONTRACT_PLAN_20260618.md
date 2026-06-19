# Trading Lab T44 Adapter Contract Plan - 2026-06-18

## Goal

Add pure adapter contracts for future data providers while keeping fixtures as the only implementation.

## Contracts

- `ValueProvider`
- `PublicMarketProvider`
- `RosterContextProvider`
- `DropPressureProvider`
- `RookieContextProvider`
- `MockDraftContextProvider`
- `OpponentContextProvider`

## Guardrails

- No real file reads.
- No imports from Outcome, Rookie, Mock Draft, Drop Decision, or Master.
- No APIs.
- No generated outputs.
- Fixture providers must report `is_real_integration=False`.

## Validation

Tests confirm fixture provider compatibility, placeholder status, expected fantasy fields, and absence of real integration methods.
