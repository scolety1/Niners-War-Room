# Trading Lab Research Intake Schema Contract

Date: 2026-06-18

## Purpose

Research intake records a paper-only question before it becomes a watchlist,
strategy, risk, or paper journal note. Intake is research-only and not
investment advice.

## Required Fields

- `intake_id`
- `date`
- `research_question`
- `asset_or_topic_scope`
- `source_names`
- `source_review_status`
- `paper_only_intent`
- `expected_learning_goal`
- `risk_categories_to_review`
- `prohibited_content_check`
- `next_review_date`
- `status`

## Optional Fields

- `operator`
- `related_watchlist_note_id`
- `related_strategy_note_id`
- `related_risk_id`
- `related_paper_journal_id`
- `notes`

## Accepted Statuses

- `IDEA`
- `SOURCE_REVIEW`
- `HOLD_NEEDS_REVIEW`
- `REJECTED_PROHIBITED`
- `READY_FOR_WATCHLIST_NOTE`
- `READY_FOR_RISK_REVIEW`
- `CLOSED_NO_ACTION`

## Invalid Fields

Reject fields that imply:

- Broker credentials, tokens, keys, or secrets
- Private account balances, holdings, fills, or exports
- Broker/API dependency
- Order placement or execution routing
- Automated triggers
- Production investment advice
- Data ingestion or generated outputs

## Paper-Only Constraints

- `paper_only_intent` must be explicit.
- `research_question` must be neutral and not advice.
- `source_review_status` must be public-source review or HOLD.
- `prohibited_content_check` must confirm no secrets, no broker/API, no private
  account data, no execution, and no advice language.

## Invalid Examples

| invalid_example | reason |
| --- | --- |
| `buy EXMPL now` | Investment advice and real-money instruction. |
| `use broker API token` | Broker/API and secret dependency. |
| `based on my account balance` | Private account data. |
| `auto-execute on threshold` | Automated execution. |
