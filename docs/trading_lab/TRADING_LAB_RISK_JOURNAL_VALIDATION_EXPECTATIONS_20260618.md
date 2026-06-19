# Trading Lab Risk Journal Validation Expectations

Date: 2026-06-18

## Purpose

Risk journal entries are research/process notes. They identify weaknesses in
paper analysis, not real account risk management or investment advice.

## Safe Risk Categories

Safe entries may cover:

- Thesis risk
- Data-quality risk
- Survivorship bias
- Look-ahead bias
- Overfitting
- Liquidity assumption risk
- Emotional/process risk
- Execution-policy risk
- Attribution or license uncertainty

## Validation Examples

| example | expected_result | why |
| --- | --- | --- |
| Paper hypothesis may overstate one public filing item | ACCEPT | Thesis risk, research-only. |
| Future universe may omit stale or delisted symbols | ACCEPT | Survivorship bias warning. |
| Public data revision may change interpretation | ACCEPT | Data-quality and look-ahead risk. |
| Repeated parameter tweaks may overfit a paper design | ACCEPT | Overfitting risk. |
| Note may drift into advice language | ACCEPT | Execution-policy/process risk. |
| `Place stop-loss order if risk rises` | REJECT | Broker order instruction. |
| `Reduce real position based on my balance` | REJECT | Real-money instruction and private account data. |
| `Connect broker to monitor risk` | REJECT | Broker integration. |
| `Auto-execute risk rule` | REJECT | Automated execution. |
| `Use private account export to measure risk` | REJECT | Private brokerage data. |

## Safe Use Reminder

Risk journal validation should keep notes descriptive, paper-only, and
non-executing. It must not produce personalized advice, account management, or
broker instructions.
