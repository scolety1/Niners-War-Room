# Trading Lab Backtesting Readiness Checklist

Date: 2026-06-18

## Purpose

This checklist defines what must exist before any future backtesting code is
allowed. It does not approve implementation, data ingestion, generated outputs,
broker/API access, app wiring, deployment, or investment advice.

Any future backtesting code requires separate explicit approval.

## Required Before Future Code

| checklist_item | required_status |
| --- | --- |
| Source policy | Approved and current. |
| Data licensing/terms review | Public source terms reviewed and documented. |
| Public-only data approval | Source list approved for public/research-only use. |
| No secrets | No keys, tokens, credentials, cookies, or `.env` files. |
| No broker/API access | No broker package, auth flow, order endpoint, or account connection. |
| No private account data | No balances, holdings, fills, statements, exports, or screenshots. |
| No generated artifacts tracked | Output paths, if any, remain untracked unless separately approved. |
| Bias controls | Survivorship, look-ahead, and revision risks documented. |
| Transaction-cost assumptions | Stated before any result review. |
| Slippage assumptions | Stated before any result review. |
| Benchmark assumptions | Neutral benchmark or no-action baseline documented. |
| Validation tests | Trading Lab-only validators and focused tests defined. |
| Closeout review | Phase closeout must list files, validation, and guardrail status. |

## HOLD Conditions

Future backtesting remains HOLD if:

- A source requires credentials or private account access.
- The universe cannot be explained.
- Licensing or storage policy is unclear.
- Generated outputs would be committed without approval.
- The design includes order placement, broker routing, or automation.
- The result would be framed as production investment advice.

## Safe Use Reminder

This checklist is a readiness gate only. It does not create or approve a
backtesting engine.
