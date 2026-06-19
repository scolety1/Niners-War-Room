# Trading Lab Risk Journal Template

Date: 2026-06-18

## Purpose

This template supports research-only risk review. It is for paper-analysis
hygiene, not real account guidance, investment advice, broker execution,
deployment, data ingestion, or generated market artifacts.

All examples are fake/public-only and must not reference private account data.

## Required Fields

Each risk journal entry should include:

- `risk_id`
- `date`
- `research_area`
- `risk_category`
- `risk_description`
- `severity_estimate`
- `probability_estimate`
- `mitigation_note`
- `invalidation_or_stop_condition`
- `review_owner`
- `review_date`
- `status`
- `notes`

## Risk Categories To Consider

- Thesis risk
- Data quality risk
- Survivorship bias
- Look-ahead bias
- Overfitting
- Liquidity assumption risk
- Execution-policy risk
- Emotional/process risk
- Attribution or license uncertainty
- Private-data contamination risk

## Valid Fake Examples

| risk_id | date | research_area | risk_category | risk_description | severity_estimate | probability_estimate | mitigation_note | invalidation_or_stop_condition | review_owner | review_date | status | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `RJ-001` | 2026-06-18 | Public filing notes | Thesis risk | Paper hypothesis may overstate one public filing item. | Medium | Medium | Require at least two public source checks before paper review. | Stop if no public citation exists. | Trading Lab HQ | 2026-07-18 | Open | Research-only, not advice. |
| `RJ-002` | 2026-06-18 | Future backtest design | Survivorship bias | A future universe may omit delisted or stale symbols. | High | Medium | Document universe construction before any code exists. | Hold if universe source cannot be explained. | Trading Lab HQ | 2026-08-18 | Open | No data ingestion approved. |
| `RJ-003` | 2026-06-18 | Paper process | Emotional/process risk | Notes may drift from observation into advice language. | Medium | Medium | Use paper-only status and invalidation fields on every note. | Stop if note contains buy/sell/order language. | Trading Lab HQ | 2026-07-01 | Open | Keep wording neutral. |

## Invalid And Prohibited Examples

| prohibited_item | why_blocked |
| --- | --- |
| Account drawdown from a private brokerage export | Private account data is prohibited. |
| Risk rule to place a stop-loss order | Broker orders and execution instructions are prohibited. |
| Auto-execute when risk threshold is hit | Automated execution is prohibited. |
| Token-protected data dump review | Secrets, credentials, and unapproved private data are prohibited. |

## Safe Use Reminder

Risk journal entries may help identify research weakness, process errors, and
paper-only review stops. They must not become production investment advice,
real account risk management, broker instructions, or automated trading rules.
