# Trading Lab Paper Journal Schema V2

Date: 2026-06-18

## Purpose

Paper Journal Schema V2 expands paper-action and review statuses while keeping
journal entries non-executing, research-only, and not investment advice.

## Required Fields

- `journal_id`
- `date`
- `symbol_or_topic`
- `asset_type`
- `research_question`
- `paper_action_type`
- `hypothetical_entry_reference`
- `hypothetical_exit_reference`
- `position_sizing_hypothesis`
- `risk_hypothesis`
- `invalidation_condition`
- `review_status`
- `outcome_review_date`
- `lessons_learned`
- `status`

## Optional Fields

- `related_intake_id`
- `related_watchlist_note_id`
- `related_strategy_note_id`
- `related_risk_id`
- `notes`

## Paper Action Statuses

- `NO_ACTION_OBSERVATION`
- `HYPOTHETICAL_ENTRY_NOTE`
- `HYPOTHETICAL_EXIT_NOTE`
- `HYPOTHETICAL_HOLD_NOTE`
- `CONTEXT_ONLY_NOTE`
- `CLOSED_PAPER_REVIEW`

## Review Statuses

- `OPEN`
- `REVIEW_DUE`
- `REVIEWED_LESSONS_CAPTURED`
- `HOLD_NEEDS_REVIEW`
- `REJECTED_PROHIBITED`

## Prohibited Execution Wording

Reject entries with:

- `place order`
- `submit order`
- `send order`
- `execute`
- `auto-execute`
- `broker API`
- `order endpoint`
- `real-money`
- `live trading`

## Invalid Examples

- Entry based on a brokerage balance
- Entry importing private brokerage export
- Entry containing API key, token, or secret
- Entry instructing buy/sell now
- Entry using generated market data without approval
