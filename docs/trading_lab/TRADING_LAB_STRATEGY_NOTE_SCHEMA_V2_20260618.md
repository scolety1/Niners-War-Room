# Trading Lab Strategy Note Schema V2

Date: 2026-06-18

## Purpose

Strategy Note Schema V2 defines validation expectations for research-only
strategy notes. Strategy notes are not investment advice and do not authorize
backtesting code, data ingestion, broker/API integration, execution, or
deployment.

## Required Fields

- `strategy_note_id`
- `date`
- `title`
- `market_or_asset_class`
- `research_question`
- `hypothesis`
- `assumptions`
- `evidence_sources`
- `risks`
- `invalidation_conditions`
- `paper_test_design`
- `review_cadence`
- `status`

## Validation Expectations

Hypotheses:

- Must be phrased as paper-only research questions.
- Must not instruct buy/sell/hold behavior.

Assumptions:

- Must be explicit.
- Must not depend on private account data, broker connectivity, or secrets.

Evidence:

- Must cite public sources or mark `HOLD_NEEDS_REVIEW`.
- Must not include private data dumps or generated datasets.

Risks:

- Must include process, source, bias, or hypothesis risk.
- Must not become real account risk guidance.

Invalidation:

- Must define when to close, hold, or reject the note.
- Must not define order triggers or automated execution rules.

## Accepted Statuses

- `DRAFT_RESEARCH`
- `SOURCE_REVIEW`
- `RISK_REVIEW`
- `PAPER_TEST_DESIGN_ONLY`
- `HOLD_NEEDS_REVIEW`
- `CLOSED_LESSONS`
- `REJECTED_PROHIBITED`

## Invalid Examples

- `buy now`
- `sell now`
- `send broker order`
- `connect broker`
- `use account balance`
- `auto-execute`
- `store API key`
