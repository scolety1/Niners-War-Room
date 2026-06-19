# Trading Lab T34 Fixture Provider Plan - 2026-06-18

## Goal

Add a safe in-memory fixture provider that mimics future fantasy trade value shape without using real data.

## Fixtures

- Target Player
- Player A
- Player B
- Player C
- Player D
- 2026 2nd
- 2026 3rd
- Team Alpha
- Team Bravo
- Team Charlie

## Guardrails

- Fixture-only fake values.
- NWR value and public fantasy market value remain separate.
- No file reads.
- No real roster imports.
- No public source integrations.
- No generated outputs.

## Validation

- Fixture provider tests cover players, picks, teams, value separation, and fake-only names.
