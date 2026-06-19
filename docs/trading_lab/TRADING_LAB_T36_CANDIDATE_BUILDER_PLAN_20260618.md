# Trading Lab T36 Candidate Builder Plan - 2026-06-18

## Goal

Generate deterministic fixture-only candidate trade packages for Trade Lab modes.

## Helpers

- `build_trade_for_candidates`
- `build_trade_away_candidates`
- `build_upgrade_position_candidates`
- `build_pick_conversion_candidates`
- `build_drop_pressure_candidates`
- `rank_candidate_packages`

## Guardrails

- Fixture provider values only.
- No real data imports.
- No file I/O.
- No external integrations.
- No broad app wiring.

## Validation

Tests cover ranked Trade For and Trade Away outputs, scoring fields, ladder placeholder notes, and no real data behavior.
