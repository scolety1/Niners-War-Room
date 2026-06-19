# Trading Lab Corrected Fantasy Trade Lab Charter

Date: 2026-06-18

## Purpose

Trading Lab is a fantasy football trade value calculator and trade package
simulator for Niners War Room.

Core product sentence:

Trading Lab helps identify realistic fantasy football trades where public
fantasy market value makes the deal acceptable, but NWR private value says the
move improves our roster.

## Non-Purpose

Trading Lab is not a stock trading, broker API, real-money finance, market-data
API, automated trade execution, or investment advice product. It is also not a
replacement for human fantasy manager review.

## Core Workflows

- Trade-for mode: start with a target player and identify what we can give up.
- Trade-away mode: start with an outgoing player and identify return targets.
- Package builder: compare multi-player and pick packages.
- Opponent fit: find the best fantasy team trade partner.
- Roster aftermath: show keeper, drop, and draft-plan impact after a proposed
  trade.
- Negotiation ladder: define opening offer, fair offer, max offer, and
  walk-away line.

## Trade-For Mode

Trade-for mode answers: I want to trade for this player. What should I give up?
It should compare NWR private value gain, public fantasy market fairness, roster
fit, and opponent needs.

## Trade-Away Mode

Trade-away mode answers: I want to trade away this player. What should I target
in return? It should rank return packages by NWR value delta, realism, roster
aftermath, and keeper/drop effects.

## Package Builder

The package builder compares give/get assets, picks, NWR value delta, public
fantasy market fairness, opponent fit, and risk flags. It does not send offers
or automate decisions.

## Opponent Fit

Opponent fit evaluates whether another fantasy manager has roster needs,
surplus, pick context, or team direction that could make a package realistic.

## Roster Aftermath

Roster aftermath should explain keeper impact, drop pressure, lineup depth,
rookie pick context, and draft-plan effects after the hypothetical trade.

## Public Fantasy Market Value

Public fantasy market value is display and comparison only. It helps estimate
whether the other manager may consider the deal fair. It must not overwrite NWR
private value.

## NWR Private Value

NWR private value is the core edge. Trading Lab should search for trades where
NWR value improves our roster while public fantasy market value keeps the offer
realistic.

## Explicit Non-Goals

- Stock trading
- Broker APIs
- Real-money finance
- Market-data APIs
- Automated trade execution
- Investment advice
- Automated fantasy trade acceptance or submission
- Cross-lane app behavior changes before explicit approval
