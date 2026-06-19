# Trading Lab Paper Journal Validation Expectations

Date: 2026-06-18

## Purpose

Paper journal validation keeps entries paper-only, research-only, and separate
from real-money trading, broker workflows, credentials, private account data,
automated execution, and investment advice.

## Valid Content

A valid paper journal entry may contain:

- Fictional symbol or research topic
- Public/manual reference notes
- Hypothetical paper entry and exit references
- Fictional position sizing hypothesis
- Research question
- Risk hypothesis
- Invalidation condition
- Outcome review date
- Lessons learned
- Paper-only status

## Rejected Content

Reject entries containing:

- Real order placement
- Broker account balances
- Private brokerage exports
- API keys, tokens, secrets, or credential-like values
- Auto-execution rules
- Personalized buy/sell/hold advice
- Private holdings or fills

## Validation Examples

| example | expected_result | why |
| --- | --- | --- |
| `PJ-EXMPL-001` with fictional symbol, paper-only status, and public reference note | ACCEPT | Safe paper journal content. |
| Context-only macro note with no position and public source citation | ACCEPT | Research-only and non-executing. |
| Entry says `place a real order now` | REJECT | Real order placement is prohibited. |
| Entry sizes using `brokerage balance` | REJECT | Private account balance language is prohibited. |
| Entry imports `private brokerage export` | REJECT | Private brokerage export is prohibited. |
| Entry includes `Bearer abc...` token text | REJECT | Secret-like values are prohibited. |
| Entry says `auto-execute if price crosses X` | REJECT | Automated execution is prohibited. |
| Entry says `buy now for your account` | REJECT | Personalized investment advice and real-money trading language. |

## Difference From Trading Execution

Paper journal validation records research hygiene. It does not place orders,
connect brokers, fetch market data, manage accounts, generate signals, or
recommend trades.
