# Trading Lab Backtesting Design Guardrails

Date: 2026-06-18

## Purpose

This document defines guardrails for future backtesting design. It does not
approve code, data ingestion, generated datasets, broker/API integration,
execution automation, deployment, or production investment advice.

Future backtesting, if approved later, must remain research/simulation-only.

## Allowed Future Simulation Inputs

Allowed inputs may be considered only after a later explicit phase gate:

- Public market data with documented source and usage terms
- Public company filings
- Public economic data
- Public event/calendar references
- Manually written paper research notes
- Simulated watchlist or portfolio assumptions

No input is approved for ingestion in this document.

## Prohibited Inputs

Future backtesting must not use:

- Broker credentials
- Account keys
- API tokens or secrets
- Private brokerage data
- Real-money order history
- Private account balances or holdings
- Automated trading endpoints
- Paid/private data dumps unless explicitly approved later
- Local raw data committed to the repo
- Generated artifacts promoted without a manifest and review gate

## Survivorship Bias Warning

Any future design must explain how the study universe is built and whether it
omits delisted, stale, renamed, or otherwise unavailable symbols. If that cannot
be explained, the design remains HOLD.

## Look-Ahead Bias Warning

Future paper simulations must not use information that would not have been
available at the hypothetical review time. Source dates, filing dates, revision
dates, and event dates must be documented.

## Overfitting Warning

Simple rules can appear useful after repeated tweaking. Future designs must
limit parameter searches, record assumptions before review, and separate
research questions from conclusions.

## Transaction-Cost Assumptions

Any future paper simulation design must state whether transaction costs are
ignored, estimated, or stress-tested. These assumptions are research-only and
must not become trading advice.

## Slippage Assumptions

Any future design must state whether slippage is ignored, estimated, or
stress-tested. Designs that depend on unrealistic fills remain HOLD.

## Benchmark Comparison Expectations

Future paper simulations should define a neutral comparison, such as a public
index or no-action paper baseline, before results are reviewed.

## Recordkeeping Expectations

Future designs should record:

- Source names and citations
- Data dates and review dates
- Universe definition
- Assumptions
- Known limitations
- Bias checks
- Output paths, if any
- Files that must remain untracked
- Reviewer and review status

## Minimum Review Before Code

Before any backtesting code exists, Trading Lab needs a later explicit approval
covering source permissions, storage policy, generated output policy, bias
checks, validation commands, and no-execution guardrails.

No broker/API execution, account connection, credential storage, app wiring, or
deployment is allowed.
