# Trading Lab T30 Desktop QA Plan - 2026-06-18

## Starting Head

T30 starts from the GREEN T29 commit on `work/trading-lab`.

## Goal

Create a desktop review checklist and route smoke coverage for the fake-data Trade Lab page.

## Files Expected To Touch

- `docs/trading_lab/`
- `tests/test_trading_lab_t30_route_smoke.py`
- Read-only inspection of `app/pages/11_trade_lab.py`

## No-Go Areas

- No real NWR data integration.
- No public fantasy trade-value API integration.
- No app shell or navigation rewiring.
- No generated outputs, deployment, data files, secrets, credentials, or execution logic.

## Validation Plan

- `git diff --check`
- Focused Trading Lab pytest suite.
- Ruff over Trading Lab source, tests, and the isolated page.
