# Trading Lab T40 UI Calculator Connection Plan - 2026-06-18

## Goal

Connect the existing desktop UI helper surface to the fixture-backed calculator layers.

## Source Layers Used

- Fixture provider.
- Candidate package builder.
- Scoring primitives.
- Negotiation ladder generator.
- Roster aftermath helpers.
- Warning engine.

## Guardrails

- No real data integration.
- No public fantasy source integration.
- No generated outputs.
- No broad app wiring.
- Keep `app/pages/11_trade_lab.py` isolated.

## Validation

Tests confirm fixture-backed packages, mode-specific output, best trade scoring, generated ladder, generated roster aftermath, warnings, and not-wired placeholders.
