# Trading Lab T22 Desktop UI Smoke Plan

Date: 2026-06-18

## Starting HEAD

`d92f17c78dcbc257005fc7899b78a725957556d1`

## Current Routed Page Status

Trading Lab is routed as one isolated Streamlit page:

- `app/pages/11_trade_lab.py`

The reusable page/component code lives under `src/trading_lab/`.

## Desktop-First Polish Goals

- Make the top header clearer.
- Improve mode selection copy.
- Group the left control panel by trade question, package constraints, and
  preference controls.
- Strengthen best trade card hierarchy.
- Improve ranked package card readability.
- Clarify the negotiation ladder.
- Clarify bad trade warnings.
- Clarify right-side roster aftermath/context.
- Make placeholder language explicit for unavailable real integrations.

## Files Expected To Touch

- `docs/trading_lab/`
- `src/trading_lab/trade_lab_component.py`
- `tests/test_trading_lab_*.py`
- `app/pages/11_trade_lab.py` only if the isolated page needs a direct polish
  change.

## No-Go Areas

- No Outcome, Rookie, Mock Draft, Drop Decision, Deployment V2, or Master files.
- No data ingestion.
- No public fantasy trade-value API integration.
- No real NWR data imports.
- No generated outputs.
- No deployment.
- No stock-market, broker, crypto, equity, or real-money product framing.

## Validation Plan

```powershell
git status --short
git diff --check
git diff --stat
python -m pytest tests/test_trading_lab_*.py -q
python -m ruff check src/trading_lab tests/test_trading_lab_*.py app/pages/11_trade_lab.py
```
