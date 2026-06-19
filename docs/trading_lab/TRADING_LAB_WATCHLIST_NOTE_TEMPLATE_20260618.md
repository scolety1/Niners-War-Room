# Trading Lab Watchlist Note Template

Date: 2026-06-18

## Purpose

Watchlist notes are paper/research-only records for learning, tracking public
observations, and preparing later paper simulation ideas. They are not
personalized investment advice and must not tell anyone to buy, sell, hold,
short, hedge, place orders, connect a broker, use credentials, or auto-execute
anything.

This template creates no execution path, broker integration, data ingestion,
generated output, private account workflow, credential storage, or deployment
path.

## Allowed Fields

Each watchlist note should use these fields:

- `ticker_or_symbol`
- `asset_type`
- `thesis_summary`
- `research_question`
- `evidence_links_or_source_names`
- `risk_notes`
- `invalidation_notes`
- `paper_only_status`
- `review_date`
- `decision_status`
- `notes`

## Field Expectations

- `ticker_or_symbol`: Public ticker, symbol, or fake placeholder used for
  paper-only notes.
- `asset_type`: Broad public label such as equity, ETF, public index, economic
  series, or fake placeholder.
- `thesis_summary`: Research hypothesis, not advice.
- `research_question`: What the note is trying to learn.
- `evidence_links_or_source_names`: Public sources or source names only.
- `risk_notes`: Research risks, data-quality risks, or process risks.
- `invalidation_notes`: What would make the paper hypothesis less useful.
- `paper_only_status`: Must clearly say paper-only.
- `review_date`: Use `YYYY-MM-DD`.
- `decision_status`: Use research statuses such as observe, review later,
  needs more public evidence, or closed paper note.
- `notes`: Optional research-only notes without private account data.

## Valid Fake Example Entries

These examples are fake/public-only examples. They are not trade
recommendations.

### Example 1

| field | value |
| --- | --- |
| ticker_or_symbol | `FAKE` |
| asset_type | Fake equity placeholder |
| thesis_summary | Paper-only observation that a public filing trend may deserve follow-up. |
| research_question | Does the next public filing confirm or weaken the paper hypothesis? |
| evidence_links_or_source_names | SEC EDGAR public filings; company investor relations page |
| risk_notes | Filing interpretation may be incomplete without broader context. |
| invalidation_notes | Close the paper note if later public filings contradict the trend. |
| paper_only_status | Paper-only research note |
| review_date | 2026-06-18 |
| decision_status | Observe for future paper review |
| notes | No real holdings, account sizing, orders, or private account data. |

### Example 2

| field | value |
| --- | --- |
| ticker_or_symbol | `FRED:FAKE_SERIES` |
| asset_type | Fake economic series placeholder |
| thesis_summary | Paper-only macro context note for learning how public data changes over time. |
| research_question | Which public macro indicators are useful context for future research notes? |
| evidence_links_or_source_names | FRED public economic data |
| risk_notes | Public series revisions may change historical interpretation. |
| invalidation_notes | Mark stale if the source definition or series availability changes. |
| paper_only_status | Paper-only research note |
| review_date | 2026-06-18 |
| decision_status | Needs more public evidence |
| notes | Descriptive context only; not a signal, recommendation, or execution plan. |

### Example 3

| field | value |
| --- | --- |
| ticker_or_symbol | `WATCHLIST-PLACEHOLDER-001` |
| asset_type | Simulated watchlist placeholder |
| thesis_summary | Paper-only exercise for practicing watchlist discipline. |
| research_question | Can the note separate public evidence from speculation? |
| evidence_links_or_source_names | Manually written paper-research note; exchange symbol reference page |
| risk_notes | Placeholder may be too abstract to teach useful review habits. |
| invalidation_notes | Close if no public source can be cited. |
| paper_only_status | Paper-only research note |
| review_date | 2026-06-18 |
| decision_status | Review later |
| notes | No private brokerage data, no generated output, no account fields. |

## Invalid And Prohibited Examples

The following examples are intentionally invalid and must not be used:

| prohibited_text | why_blocked |
| --- | --- |
| Buy 100 shares now | Direct real-money trading instruction and investment advice. |
| Place stop-loss order | Broker order and execution instruction. |
| Use broker token | Credential/token use is prohibited. |
| Auto-execute if price crosses X | Automated execution path is prohibited. |
| Based on my private brokerage balance | Private account data is prohibited. |

## Safe Use Reminder

Watchlist notes may support learning, public-source tracking, risk thinking,
and later paper simulation only. They must not include personalized investment
advice, private account information, real holdings, order instructions, broker
credentials, automation rules, generated artifacts, or deployment plans.
