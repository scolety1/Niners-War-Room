# Trading Lab Charter

Date: 2026-06-18

## Purpose

Trading Lab is a separate Niners War Room research lane for market learning,
paper trading, market analysis tooling design, watchlists, backtesting design,
risk journaling, and strategy notes.

The lane exists to support education, structured research, and simulation-only
work. It must not create real-money trading behavior, broker connectivity,
production investment advice, public deployment paths, or changes to any
fantasy football lane.

## Non-Purpose

Trading Lab is not a trading execution system, brokerage integration, account
management tool, investment advisory product, public application, or deployment
lane.

It must not place trades, recommend trades for production use, store secrets,
handle private brokerage account data, automate execution, or connect to broker
order endpoints.

## Scope

Allowed T1 scope is docs-only and limited to:

- Trading Lab charter definition
- Source and data policy
- Paper-trading-only workflow design
- Source inventory planning
- Watchlist structure planning
- Strategy-note structure planning
- Backtesting-design questions
- Risk journal structure
- Paper-trade journal structure
- Future phase gates

Future phases may be proposed only as gated possibilities. T1 does not open
code, data ingestion, simulation tooling, broker integration, deployment, or
automated execution.

## Hard Prohibitions

Trading Lab must not create, perform, store, or enable:

- Real-money trading
- Broker orders
- Broker API trading integration
- Live credentials or secrets
- Account keys
- Automated execution
- Production investment advice
- Public deployment
- Secret storage
- Private account data unless a later explicit approval exists

These prohibitions apply to documentation, examples, code, configuration,
sample files, and future phase proposals.

## Education And Research Only

Trading Lab work must be framed as education, research, and process design. It
may compare public information, define study questions, record observations,
and document paper-only workflows.

Trading Lab must not present conclusions as production investment advice. Any
metrics, screens, notes, or simulated results must be treated as research inputs
for learning and review, not instructions to buy, sell, hold, short, hedge, or
otherwise trade with real money.

## Paper And Simulation Only

All trading workflows in this lane are paper-only or simulation-only. Paper
trades may be manually recorded as research journal entries. Simulated
portfolio or watchlist files may be proposed in future phases, but T1 does not
create data files, ingestion tooling, execution tooling, or broker connections.

No workflow may cross from paper research into real-money execution without a
separate explicit approval and a new phase gate. Even then, the current hard
guardrails prohibit broker orders, automated execution, live credentials, and
broker API trading integration in this repo.

## Relationship To Niners War Room Lanes

Trading Lab is separate from the Niners War Room fantasy football lanes and
must not touch their repos, app behavior, artifacts, or deployment flows.

Out of scope fantasy lanes include:

- Outcome
- Rookie
- Mock Draft
- Drop Decision
- Deployment V2
- Master

Trading Lab must not change app behavior, projections, rankings, probabilities,
draft workflows, promoted artifacts, hidden sort keys, simulations, release
notes, deployment scripts, or user-facing fantasy football workflows.

## Phase T1 Boundary

Phase T1 is open only for charter, source inventory, source/data policy, and
paper-trading research plan documents.

T1 is GREEN only while all work remains docs-only, education-only,
paper/simulation-only, and separated from fantasy football lanes.
