# Trading Lab T37 Negotiation Engine Plan - 2026-06-18

## Goal

Generate manual negotiation ladder text from fixture-backed package values.

## Helpers

- `build_opening_offer`
- `build_fair_offer`
- `build_max_offer`
- `build_walk_away_line`
- `build_counteroffer_notes`
- `build_do_not_include_assets`
- `build_negotiation_ladder`

## Guardrails

- Fake fixture packages only.
- No automatic sending.
- No automated decisioning.
- No league transaction submission.
- No real platform integration.

## Validation

Tests confirm ladder fields, do-not-include assets, counteroffer notes, high-gain behavior, and no submission language.
