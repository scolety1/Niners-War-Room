# Trading Lab Fixture Calculator Review Packet - 2026-06-18

## Purpose

Trading Lab is a fantasy football trade value calculator and trade package simulator for Niners War Room. The fixture-backed MVP supports desktop review before any real data integration.

## How To Open The Page

- Isolated Streamlit page: `app/pages/11_trade_lab.py`

## What Is Now Fixture-Backed

- Fantasy asset contracts for players and rookie picks.
- Fake fixture provider for players, picks, and teams.
- Candidate package builder for key Trade Lab modes.
- NWR value delta scoring.
- Public fantasy market delta scoring.
- Market fairness labels.
- Opponent fit labels.
- Roster impact labels.
- Keeper/drop impact labels.
- Negotiation ladder generation.
- Roster aftermath generation.
- Bad trade warning generation.

## What Is Still Fake

- All players, picks, teams, values, roster contexts, and warnings.
- All NWR private values.
- All public fantasy market values.
- All opponent roster contexts.
- All rookie/mock draft context.

## What Scoring Does

- Compares fixture NWR value received against fixture NWR value given.
- Separately compares fixture public fantasy market value received against value given.
- Labels market realism, opponent fit, roster impact, keeper/drop impact, and risk.
- Produces manual review verdicts.

## What Scoring Does Not Do

- It does not use real NWR outputs.
- It does not use public fantasy data sources.
- It does not optimize against real player datasets.
- It does not submit, send, or execute trades.
- It does not make automatic league transaction decisions.

## NWR And Public Value Separation

NWR private value and public fantasy market value are stored in separate fields on each fixture asset. The scoring helpers calculate `nwr_delta` and `public_market_delta` independently so public value never overwrites NWR value.

## Negotiation Ladder

The ladder derives opening, fair, max, walk-away, do-not-include, and counteroffer notes from fixture package assets and scores. It is manual review guidance only.

## Roster Aftermath

Roster aftermath estimates keeper impact, drop pressure, position depth, and rookie/mock context from fake fixture package contents. Real roster integrations remain not wired.

## Known Placeholders

- Real NWR private value.
- Public fantasy market value sources.
- Outcome, Rookie, Mock Draft, and Drop Decision context.
- Real roster state.
- Generated review exports.

## Guardrails

- Fixture-only.
- No data ingestion.
- No public fantasy source integration.
- No generated outputs.
- No app shell wiring beyond the existing isolated page.
- No automated fantasy trade submission.

## Recommended Next Phase

Run a human desktop review of the fixture-backed MVP. A later phase can propose read-only integration discovery only with explicit approval and source boundaries.
