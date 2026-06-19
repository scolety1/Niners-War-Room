# Trading Lab Corrected UI Master Handoff

Date: 2026-06-18

## Corrected Purpose

Trading Lab is a fantasy football trade value calculator and trade package
simulator for Niners War Room.

It helps identify realistic fantasy football trades where public fantasy market
value makes the deal acceptable, but NWR private value says the move improves
our roster.

## Current UI Capability

- Desktop-first Streamlit page at `app/pages/11_trade_lab.py`.
- Three-column layout.
- Fake in-memory demo trade packages.
- Best trade card.
- Ranked package cards.
- Negotiation ladder.
- Bad trade warnings.
- Roster aftermath and keeper/drop context.
- Training Mode placeholder.

## How To Validate

```powershell
python -m pytest tests/test_trading_lab_*.py -q
python -m ruff check src/trading_lab tests/test_trading_lab_*.py app/pages/11_trade_lab.py
```

## Route / Component Status

- Route status: isolated Streamlit page.
- Component source: `src/trading_lab/trade_lab_component.py`.
- Demo model source: `src/trading_lab/trade_lab_ui.py`.
- No broader navigation or deployment changes.

## Guardrails

- No Wall Street product framing.
- No broker/API integration.
- No real-money trading.
- No automated execution or automated fantasy trade submission.
- No investment advice.
- No data ingestion.
- No public fantasy trade-value API integration yet.
- No real Outcome/Rookie/Mock Draft/Drop Decision integration yet.
- No generated outputs.
- No deployment.

## Next Recommended Step

Review the isolated Trade Lab page with fake data. If accepted, the next safe
phase is a narrow, explicitly approved data-contract phase for connecting NWR
private value and public fantasy market comparison placeholders.
