# Trading Lab Watchlist Examples

Date: 2026-06-18

## Purpose

These examples show safe and unsafe watchlist-note patterns. Safe examples use
fictional symbols or public source names and remain paper/research-only. They
are not recommendations, trading signals, or investment advice.

## Safe Examples

### Equity Research Question

| field | value |
| --- | --- |
| ticker_or_symbol | `EXMPL` |
| asset_type | Fictional equity placeholder |
| thesis_summary | Public filing trend may be worth a paper-only follow-up. |
| research_question | Does the next public filing support or weaken the hypothesis? |
| evidence_links_or_source_names | SEC EDGAR public filings |
| risk_notes | Single-source interpretation may be incomplete. |
| invalidation_notes | Close if no second public source can support the observation. |
| paper_only_status | Paper-only research note |
| decision_status | Observe |

### ETF/Index Research Question

| field | value |
| --- | --- |
| ticker_or_symbol | `PAPER-IDX` |
| asset_type | Fictional index placeholder |
| thesis_summary | Research how broad public index context changes watchlist notes. |
| research_question | Does an index baseline make paper notes less narrative-driven? |
| evidence_links_or_source_names | Exchange-published reference page |
| risk_notes | Index composition and definitions may change. |
| invalidation_notes | Hold if public source cannot be attributed. |
| paper_only_status | Paper-only research note |
| decision_status | Needs more public evidence |

### Macro/Economic Indicator Watch Item

| field | value |
| --- | --- |
| ticker_or_symbol | `FRED-PAPER-SERIES` |
| asset_type | Fictional economic series placeholder |
| thesis_summary | Macro series may provide useful context for later research notes. |
| research_question | Which public economic indicators are descriptive rather than predictive? |
| evidence_links_or_source_names | FRED public economic data |
| risk_notes | Revisions and reporting lag can change interpretation. |
| invalidation_notes | Mark stale if source definition changes. |
| paper_only_status | Paper-only research note |
| decision_status | Review later |

### Earnings-Event Research Question

| field | value |
| --- | --- |
| ticker_or_symbol | `PAPER-EARN` |
| asset_type | Fictional event-study placeholder |
| thesis_summary | Public earnings calendar quality may affect paper event notes. |
| research_question | How often do public event dates need later correction? |
| evidence_links_or_source_names | Public earnings calendar reference |
| risk_notes | Event dates can be revised or reported inconsistently. |
| invalidation_notes | Hold if event source is not public or attributable. |
| paper_only_status | Paper-only research note |
| decision_status | Observe |

## Invalid Examples

### Invalid Broker Credential Item

| field | invalid_value | why_rejected |
| --- | --- | --- |
| notes | Use broker token to pull account positions. | Credentials, broker integration, and private account data are prohibited. |

### Invalid Execution Command Item

| field | invalid_value | why_rejected |
| --- | --- | --- |
| thesis_summary | Auto-execute if `EXMPL` crosses a target price. | Automated execution and order logic are prohibited. |

### Invalid Personalized Advice Item

| field | invalid_value | why_rejected |
| --- | --- | --- |
| decision_status | Buy 100 shares now based on my private brokerage balance. | Investment advice, real-money trading, and private account data are prohibited. |

## Safe Use Reminder

Watchlist examples may teach note structure and guardrail checks. They must not
include real account holdings, order instructions, broker tokens, private
balances, automated triggers, generated datasets, deployment plans, or
personalized investment advice.
