# Trading Lab Paper Research Plan

Date: 2026-06-18

## Purpose

This plan defines a paper-trading-only research workflow for Trading Lab T1.
It is designed for education, observation, and process development without
creating trading recommendations, broker integration, data ingestion, execution
automation, or deployment.

## Watchlist Design

Future watchlists should be structured as research objects, not trade
recommendations. A watchlist entry may describe:

- Ticker or instrument identifier from a public source
- Research theme
- Public source references
- Hypothesis being observed
- Key dates or events to monitor
- Risk notes
- Paper-only status
- Review date

Watchlists must not include real account holdings, account sizing, live order
instructions, broker account fields, or production advice.

## Strategy-Note Design

Strategy notes should record learning questions and paper-only hypotheses. A
note may include:

- Strategy label
- Market condition being studied
- Public source inputs
- Entry hypothesis for paper review
- Exit hypothesis for paper review
- Risk hypothesis
- Invalidating conditions
- Known limitations
- Review outcome

Strategy notes must clearly distinguish observation from recommendation. They
must not tell a reader to buy, sell, hold, short, hedge, or execute a trade
with real money.

## Backtesting-Design Questions

T1 may define backtesting questions, but it must not create backtest code,
download data, or generate artifacts.

Questions to answer before any future backtesting phase:

- What public data source would be used?
- What license, attribution, and redistribution limits apply?
- What exact universe would be studied?
- What time period would be studied?
- How would survivorship bias be handled?
- How would lookahead bias be avoided?
- What assumptions would be documented?
- What metrics would be research-only?
- What files would be generated locally?
- Which paths would remain untracked?
- What review gate would prevent trading advice or execution behavior?

No backtesting phase may open until source policy, file policy, and guardrail
checks are accepted in a later explicit approval.

## Risk Journal Design

The risk journal should focus on process discipline and research hygiene. It
may track:

- Research hypothesis risk
- Data quality concerns
- Bias concerns
- Overfitting risk
- Liquidity or volatility observations from public sources
- Paper-only sizing assumptions
- Emotional/process notes
- Lessons learned

The risk journal must not contain private account balances, broker exports,
real trade fills, live positions, account keys, or execution instructions.

## Paper-Trade Journal Design

Paper-trade journal entries may be manually recorded for simulation review.
Each entry should be labeled as paper-only and may include:

- Paper entry date
- Paper exit date if applicable
- Instrument identifier
- Research thesis
- Simulated entry price from a public reference
- Simulated exit price from a public reference
- Paper-only sizing assumption
- Risk note
- Outcome note
- Review note

Paper-trade journals must not be represented as real trading results,
production advice, or account performance.

## Review Cadence

Suggested paper research cadence:

- Weekly: review watchlist changes, source notes, and risk journal entries
- Monthly: review strategy-note quality and bias controls
- Quarterly: review whether future phase gates are still appropriate

Review cadence is a research process only. It does not imply an investment
schedule, trading signal, or execution recommendation.

## Metrics To Study

Future research may study metrics such as:

- Volatility measures
- Drawdown measures
- Win/loss distribution in simulations
- Average paper outcome
- Maximum adverse excursion
- Maximum favorable excursion
- Source coverage quality
- Hypothesis hit rate
- Review latency
- Journal completeness

Metrics must remain descriptive research aids. They must not be converted into
production investment advice, automated signals, broker orders, or live
execution decisions.

## Future Gates

Before any future code, data ingestion, simulation tooling, generated files, or
source inventory implementation, Trading Lab needs a later explicit approval
that answers:

- Is the work still education-only and paper-only?
- Does it avoid broker integration and automated execution?
- Does it avoid secrets and credentials?
- Does it avoid private account data?
- Does it keep generated files out of git?
- Does it avoid deploy and CI/CD changes?
- Does it avoid all fantasy football lanes?
- Are allowed paths and prohibited paths documented?
- Are validation commands defined before changes begin?

Until those questions are answered in a later phase, Trading Lab remains in T1
docs-only mode.
