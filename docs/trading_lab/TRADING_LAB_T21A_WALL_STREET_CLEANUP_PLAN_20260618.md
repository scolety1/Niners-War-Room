# Trading Lab T21A Wall Street Cleanup Plan

Date: 2026-06-18

## What Was Wrong

Trading Lab had been developed as a stock-market and Wall Street research lane.
That was incorrect for Niners War Room. The lane contained finance framing such
as paper trading, public market data, broker/API prohibitions, SEC/FRED
examples, backtesting, and investment-advice language.

## Corrected Purpose

Trading Lab is a fantasy football trade value calculator and trade package
simulator. It helps identify realistic fantasy football trades where public
fantasy market value makes the deal acceptable, but NWR private value says the
move improves our roster.

## Cleanup Rules

- Delete docs that are purely Wall Street or stock-market specific.
- Rewrite useful structure into fantasy trade-value language.
- Keep broker/API/real-money wording only as prohibited examples.
- Replace market data with public fantasy trade value source where appropriate.
- Replace paper trading with manual fantasy trade review or trade simulation.
- Replace backtesting with trade package scenario testing.
- Replace investment advice with fantasy trade advice or automated decisioning,
  while retaining no-investment-advice only as a safety note when needed.

## Files Expected To Delete Or Rewrite

- Delete old stock-market docs and templates.
- Delete old paper-trading tests.
- Rewrite validation-only helpers around fantasy trade package payloads.
- Add corrected charter, fantasy source policy, trade package schema, and T21A
  closeout.

## Guardrails

- No UI page yet.
- No app wiring.
- No fantasy data integration yet.
- No data ingestion.
- No generated artifacts.
- No Outcome, Rookie, Mock Draft, Drop Decision, Deployment V2, or Master edits.

## Validation Plan

```powershell
git status --short
git diff --check
git diff --stat
python -m pytest tests/test_trading_lab_*.py -q
python -m ruff check src/trading_lab tests/test_trading_lab_*.py
```

Also run an old-domain term search over `docs/trading_lab/` and explain any
remaining references.
