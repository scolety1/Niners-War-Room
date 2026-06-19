# Trading Lab T31 Placeholder Boundary Plan - 2026-06-18

## Starting Head

T31 starts from the GREEN T30 desktop QA commit on `work/trading-lab`.

## Goal

Make the fake-data boundary explicit so reviewers can tell what is available now and what requires later approval.

## Files Expected To Touch

- `docs/trading_lab/`
- `src/trading_lab/trade_lab_component.py`
- `tests/test_trading_lab_t31_placeholder_boundaries.py`

## Current Fake/In-Memory Areas

- Trade package examples.
- NWR gain display values.
- Public fantasy market fairness labels.
- Roster aftermath.
- Drop pressure context.
- Rookie/mock draft context.
- Training Mode scenarios.

## Validation Plan

- Confirm placeholder labels say `not wired` and `needs approval`.
- Confirm no placeholder claims real integration exists.
- Run focused Trading Lab tests and Ruff.
