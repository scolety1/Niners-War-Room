# Trading Lab Watchlist Note Schema V2

Date: 2026-06-18

## Purpose

Watchlist Note Schema V2 tightens paper-only watchlist structure. Watchlist
notes support learning and later paper review only. They are not advice,
signals, orders, or broker workflows.

## Required Fields

- `watchlist_note_id`
- `date`
- `ticker_or_symbol`
- `asset_type`
- `research_theme`
- `hypothesis`
- `public_sources`
- `risk_notes`
- `invalidation_notes`
- `paper_only_status`
- `review_date`
- `decision_status`

## Optional Fields

- `related_intake_id`
- `related_strategy_note_id`
- `related_risk_id`
- `notes`

## Accepted Decision Statuses

- `OBSERVE`
- `NEEDS_MORE_PUBLIC_EVIDENCE`
- `READY_FOR_RISK_REVIEW`
- `HOLD_NEEDS_REVIEW`
- `CLOSED_LESSONS`
- `REJECTED_PROHIBITED`

## Rejection Cases

Reject watchlist notes that include:

- Buy/sell/hold advice
- Order placement
- Broker/API dependency
- Credentials, secrets, keys, or tokens
- Private account data
- Automated execution
- Generated market data
- Deployment or app wiring

## Validation Expectations

- `paper_only_status` must clearly state paper-only.
- `public_sources` must not be blank unless status is `HOLD_NEEDS_REVIEW`.
- `review_date` must use `YYYY-MM-DD`.
- `hypothesis` must be framed as research, not recommendation.
- `invalidation_notes` must describe when to close or hold the paper note.
