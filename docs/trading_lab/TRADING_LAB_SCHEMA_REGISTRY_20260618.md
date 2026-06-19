# Trading Lab Schema Registry

Date: 2026-06-18

| artifact_type | required_fields | optional_fields | allowed_statuses | rejected_fields_content | validator_test_coverage | safe_next_improvement |
| --- | --- | --- | --- | --- | --- | --- |
| source_inventory | source id, name, category, intended use, access method, attribution | notes, reviewed date, config | ACCEPT, HOLD, REJECT | secrets, broker/API, private data, execution | source metadata tests | Manifest acceptance criteria |
| research_intake | intake id, date, research question, paper-only intent, status | operator, notes, review date | IDEA, SOURCE_REVIEW, HOLD, REJECTED, READY, CLOSED | advice, broker/API, credentials, private data | T7/T8 text tests | Intake dataclass later |
| manual_lifecycle | lifecycle id, from/to status, transition reason, guardrail check | operator, notes | lifecycle statuses | orders, broker credentials, auto-execution | T7/T8 text tests | T10 transition validator |
| watchlist_note | symbol, theme, hypothesis, sources, risks, paper-only, review date | notes, related ids | observe, hold, closed, rejected | advice, orders, broker/API, private data | watchlist/T7/T8 tests | V2 field validator |
| strategy_note | id, title, question, hypothesis, evidence, risks, invalidation, status | assumptions, notes | draft, source review, risk review, hold, closed, rejected | advice, broker/API, secret, execution | T7/T8 text tests | Dedicated validator |
| risk_journal | id, category, description, severity, probability, mitigation, status | owner, lessons, notes | open, mitigated, hold, closed, rejected | real account risk, broker workflow, advice | T7/T8 text tests | Dedicated validator |
| paper_journal | journal fields from schema v2 | related ids, notes | open, review due, reviewed, hold, rejected | execution, private account, secrets | paper/T7/T8 tests | Status constants |
| manual_review_packet | packet id, item id, artifact type, summaries, checks, status | lessons, next step, notes | accept, hold, rejected, closed | broker/API, execution, private data | T7/T8 text tests | T9 packet validator |
| blocked_work_gate | request text, gate status, reason | reviewer, notes | allow research, hold, reject | ingestion, generated output, broker/API | T6/T8 tests | T11 gate validator |

All schemas are for paper/research-only manual artifacts.
