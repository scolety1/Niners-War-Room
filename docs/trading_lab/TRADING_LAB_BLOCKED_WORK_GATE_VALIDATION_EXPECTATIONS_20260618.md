# Trading Lab Blocked-Work Gate Validation Expectations

Date: 2026-06-18

## Purpose

This document defines how the blocked-work gate should classify future Trading
Lab requests. The gate is a paper/research safety check only.

## ACCEPT: Research-Only

Expected result: `ALLOW_RESEARCH_ONLY`

Valid examples:

- Create a paper-only manual source review checklist.
- Add fake watchlist-note examples with risk and invalidation notes.
- Improve docs explaining prohibited language.
- Add validation-only tests for manual research artifacts.

## HOLD: Needs Explicit Future Approval

Expected result: `HOLD_NEEDS_EXPLICIT_APPROVAL`

Hold examples:

- Propose data ingestion after a separate phase review.
- Build backtesting implementation.
- Add simulation tooling.
- Create generated market datasets or generated outputs.
- Wire Trading Lab into the app.
- Add deployment or CI/CD changes.

HOLD does not mean approved. It means the work cannot begin until a later user
approval explicitly opens that future phase.

## REJECT: Prohibited

Expected result: `REJECT_PROHIBITED`

Rejected examples:

- Add broker API integration.
- Place broker orders.
- Use credentials, secrets, keys, or tokens.
- Use private brokerage exports or account balances.
- Add automated execution.
- Provide production investment advice.
- Change Outcome, Rookie, Mock Draft, Drop Decision, Deployment V2, or Master HQ
  behavior from this lane.

## Operator Rule

When a request is HOLD or REJECT, do not stage or commit related implementation.
Record the reason and keep Trading Lab paper/research-only.
