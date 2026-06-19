# Trading Lab Next Phase Options

Date: 2026-06-18

## Purpose

This document lists safe next options without approving future blocked work.
Each option must still preserve Trading Lab as research-only, paper-only, and
non-executing.

## Safe Option A: Docs-Only Operator Drill

Value:

- Tests the manual workflow with fake examples.
- Improves handoff clarity.

Allowed files:

- `docs/trading_lab/`

Blocked:

- No code, data ingestion, generated outputs, app wiring, or deployment.

## Safe Option B: Validation-Only Status Constants

Value:

- Tightens accepted statuses for paper journals, risk journals, and strategy
  notes.
- Keeps all checks in memory.

Allowed files:

- `src/trading_lab/`
- `tests/test_trading_lab_*.py`
- `docs/trading_lab/`

Blocked:

- No external data, API clients, broker models, or trading signals.

## Safe Option C: Docs-Only Manual QA Packet

Value:

- Gives Master HQ a repeatable checklist for reviewing a single research item.

Allowed files:

- `docs/trading_lab/`

Blocked:

- No market data downloads, account data, generated reports, or deployment.

## Future Work That Requires Separate Explicit Approval

- Data ingestion proposal.
- Backtesting implementation proposal.
- Simulation tooling proposal.
- App wiring proposal.
- Generated output proposal.

## Permanently Prohibited

- Real-money trading.
- Broker orders.
- Broker/API integration.
- Credentials, secrets, keys, or tokens.
- Automated execution.
- Production investment advice.
- Private brokerage/account data.
- Fantasy-football lane behavior changes.
