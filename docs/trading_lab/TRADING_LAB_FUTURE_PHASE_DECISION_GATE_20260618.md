# Trading Lab Future Phase Decision Gate

Date: 2026-06-18

## Purpose

This gate defines what must be true before future data ingestion or backtesting
implementation can even be proposed. This document does not approve future
blocked work.

## Before Data Ingestion Can Be Proposed

- Source policy is current.
- Public-only sources are named.
- License/terms review is documented.
- Storage policy is documented.
- Generated-output policy is documented.
- No secrets, credentials, keys, tokens, cookies, or `.env` are needed.
- No broker/API, order endpoint, or account connection is needed.
- No private account data is involved.
- Validation plan is limited to Trading Lab paths.
- Closeout criteria are defined.

## Before Backtesting Implementation Can Be Proposed

- Backtesting design guardrails are current.
- Public data source candidate is documented.
- Bias controls are named: survivorship, look-ahead, overfitting, revisions.
- Transaction cost and slippage assumptions are defined.
- Benchmark or no-action baseline is defined.
- Generated outputs are explicitly untracked unless separately approved.
- The proposal states no execution, no broker/API, and no advice.

## Permanently Prohibited

- Real-money trading
- Broker orders
- Broker/API trading integration
- Credentials, secrets, keys, or tokens
- Automated execution
- Production investment advice
- Public deployment
- Private brokerage/account data
- Fantasy-lane behavior changes

## Required Review Checklist

- Does the proposal remain paper/research-only?
- Are all sources public and approved for manual review?
- Are secrets and credentials absent?
- Is private account data absent?
- Is execution absent?
- Are generated outputs blocked or governed?
- Are validation commands listed?
- Is closeout required?

## Required User Approval Language

Any future proposal must include explicit user approval text naming the phase,
allowed paths, prohibited paths, validation commands, and whether generated
outputs are permitted. Without that approval, the work remains blocked.

## Required Closeout Expectations

Every future phase must close with files changed, validation results, guardrail
confirmation, remaining blocked areas, and GREEN/YELLOW/RED verdict.
