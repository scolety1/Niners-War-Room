# Trading Lab Doc Style And Terms Guide

Date: 2026-06-18

## Preferred Terms

- research-only
- paper-only
- manual review
- validation-only
- no execution path
- not investment advice
- fake example
- public/manual source review
- HOLD for explicit approval
- REJECT prohibited work

## Terms To Avoid Or Reject

- buy now
- sell now
- execute
- broker token
- private account balance
- automated order
- place order
- guaranteed return
- production investment advice
- connect broker
- ingest market data

## Rewrite Pattern

Use questions, hypotheses, evidence notes, risks, and invalidation conditions.
Do not use commands, personalized advice, execution instructions, or account
references.

## Examples

| unsafe | safer research-only phrasing |
| --- | --- |
| Buy now | Research whether the thesis still has support. |
| Sell now | Review downside evidence and invalidation notes. |
| Execute if price crosses X | Add a manual review note for a hypothetical paper scenario. |
| Use broker token | Remove the credential reference; no safe rewrite keeps it. |
| Based on my private account balance | Use hypothetical paper sizing assumptions without private data. |

## Boundary

This guide governs wording only. It does not approve data ingestion,
simulation/backtesting implementation, broker/API work, or deployment.
