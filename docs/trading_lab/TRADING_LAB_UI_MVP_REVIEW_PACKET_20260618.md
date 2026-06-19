# Trading Lab UI MVP Review Packet - 2026-06-18

## Purpose

Trading Lab is a fantasy football trade value calculator and trade package simulator. It helps review realistic fantasy trades where public fantasy market value can look fair, while NWR private value indicates whether the roster improves.

## How To Open

Open the isolated Streamlit page:

- `app/pages/11_trade_lab.py`

## What To Review On Desktop

- Header: `Trade Lab`
- Subtitle: `Find realistic fantasy trades where market says fair, but NWR says we win.`
- Left control panel for trade question, mode, target/outgoing player, opponent team, package constraints, and preferences.
- Center review board for best trade, ranked packages, negotiation ladder, and bad trade warnings.
- Right context panel for roster aftermath, keeper impact, drop pressure impact, positional depth, rookie/mock placeholder context, and data status.
- Training Mode fake scenarios and scoring dimensions.
- Placeholder integration boundary expander.

## Expected Sections

- Build the trade.
- Review candidate packages.
- Understand roster aftermath.
- Best trade.
- Ranked packages.
- Negotiation ladder.
- Bad trade warnings.
- Training Mode.
- Placeholder integration boundaries.

## What Is Fake

- Players, picks, teams, packages, scores, warnings, roster aftermath, and Training Mode scenarios.
- NWR value gains.
- Public fantasy market fairness.
- Opponent fit.
- Roster/drop/keeper context.

## What Is Not Wired

- Real NWR private value.
- Public fantasy market value sources.
- Outcome, Rookie, Mock Draft, or Drop Decision data.
- Roster files.
- Generated outputs.
- Any automated fantasy trade submission or automatic decisioning.

## Guardrails

- No Wall Street, stock-market, broker, crypto, equity, or real-money finance framing.
- No credentials, secrets, keys, or tokens.
- No data ingestion.
- No deployment.
- No fantasy-lane behavior changes.

## Recommended Next Phase

Run a human desktop review of the fake-data UI. Only after that review should a new, explicit approval decide whether a read-only integration discovery phase is appropriate.
