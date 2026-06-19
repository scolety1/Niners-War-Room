# Trading Lab Strategy Note Template

Date: 2026-06-18

## Purpose

This template defines a research-only strategy note format. Strategy notes are
for learning, paper-test design, and structured review. They are not investment
advice, trading signals, broker instructions, automated rules, or deployment
inputs.

## Required Fields

Each strategy note should include:

- `strategy_note_id`
- `title`
- `market_or_asset_class`
- `research_question`
- `hypothesis`
- `evidence_sources`
- `assumptions`
- `risks`
- `invalidation_conditions`
- `paper_test_design`
- `review_cadence`
- `status`
- `notes`

## Allowed Example Notes

These examples are research prompts only, not recommendations.

### Moving-Average Rule Study

| field | value |
| --- | --- |
| strategy_note_id | `SN-001` |
| title | Study how a moving-average rule behaves on public historical data |
| market_or_asset_class | Fictional public equity universe |
| research_question | What limitations appear when a simple rule is reviewed only as a paper study? |
| hypothesis | A simple rule may look better before costs, slippage, and bias checks. |
| evidence_sources | Public historical-data source candidates, not ingested in this phase |
| assumptions | No code or data download until a later explicit gate |
| risks | Overfitting, survivorship bias, look-ahead bias |
| invalidation_conditions | Hold if source licensing or universe construction is unclear |
| paper_test_design | Design-only note for a future paper simulation |
| review_cadence | Monthly research review |
| status | Design note |
| notes | No buy/sell instruction and no execution path |

### Earnings-Date Volatility Review

| field | value |
| --- | --- |
| strategy_note_id | `SN-002` |
| title | Compare earnings-date volatility using public calendar references |
| market_or_asset_class | Fictional equity event study |
| research_question | How often do public event dates align with observed paper volatility notes? |
| hypothesis | Calendar quality may matter more than the simple event label. |
| evidence_sources | Public earnings calendar references |
| assumptions | Manual review only; no generated datasets |
| risks | Calendar revisions, stale source pages, event survivorship |
| invalidation_conditions | Close if public event references cannot be attributed |
| paper_test_design | Paper-only event classification design |
| review_cadence | Quarterly |
| status | Research question |
| notes | Not advice and not an order plan |

### Public Macro Series Review

| field | value |
| --- | --- |
| strategy_note_id | `SN-003` |
| title | Review macro series from public economic data |
| market_or_asset_class | Public economic indicator context |
| research_question | Which public macro series are useful context for paper notes? |
| hypothesis | Some series may be descriptive but not predictive. |
| evidence_sources | FRED public economic data source names |
| assumptions | Manual citation only |
| risks | Revisions, lag, false causality |
| invalidation_conditions | Hold if source definition changes or cannot be cited |
| paper_test_design | Context-only research review |
| review_cadence | Quarterly |
| status | Observe |
| notes | No personalized advice |

## Invalid And Prohibited Notes

| prohibited_note | why_blocked |
| --- | --- |
| Buy now | Investment advice and real-money trading instruction. |
| Send order | Broker execution instruction. |
| Connect broker | Broker integration is prohibited. |
| Use account balance | Private account data is prohibited. |
| Auto-execute | Automated execution is prohibited. |

## Safe Use Reminder

Strategy notes may describe research questions and future paper-test design.
They must not include broker credentials, order language, private account data,
production advice, generated datasets, app wiring, or deployment plans.
