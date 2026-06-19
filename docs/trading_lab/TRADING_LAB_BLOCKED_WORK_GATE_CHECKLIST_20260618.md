# Trading Lab Blocked Work Gate Checklist

Date: 2026-06-18

## Purpose

This gate says what must be true before future data ingestion or backtesting can
even be proposed. It does not approve implementation.

## Proposal Preconditions

All must be true before a proposal may be written:

- Source policy is current.
- Public-only data sources are identified.
- Licensing and terms review is documented.
- Storage policy is documented.
- Generated-output policy is documented.
- No private account data is involved.
- No secrets, credentials, keys, tokens, cookies, or `.env` are involved.
- No broker/API, order endpoint, or execution path is involved.
- No app wiring or deployment is involved.
- Bias controls are named before implementation.
- Validation plan is limited to Trading Lab paths.
- Closeout criteria are defined.

## Immediate REJECT Conditions

Reject before proposal if the work requires:

- Broker/API integration
- Real-money trading or orders
- Credentials or secrets
- Automated execution
- Private brokerage/account data
- Production investment advice
- Public deployment
- Generated market datasets committed to git
- Changes to fantasy-football lanes

## HOLD Conditions

Mark HOLD if:

- Source terms are unclear.
- Storage policy is unclear.
- Output path policy is unclear.
- Validation owner is unclear.
- The request mixes research with advice.
- The request implies ingestion before a phase gate.

## Safe Proposal Scope

A future proposal may discuss design only. It must not include code, ingestion,
generated outputs, broker dependencies, credentials, deployment steps, or real
trade recommendations.
