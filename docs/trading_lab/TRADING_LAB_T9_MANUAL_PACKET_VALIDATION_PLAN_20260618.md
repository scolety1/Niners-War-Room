# Trading Lab T9 Manual Packet Validation Plan

Date: 2026-06-18

## Purpose

T9 makes manual review packets reviewable as in-memory paper/research artifacts.
The helper does not read files, write files, fetch data, connect to APIs,
execute trades, create outputs, use real account data, or wire app behavior.

## Packet Sections

- `packet_id`
- `intake_section`
- `source_review_section`
- `watchlist_section`
- `risk_review_section`
- `paper_journal_section`
- `closeout_section`

## Validation Coverage

- Missing sections return HOLD-style validation issues.
- Prohibited text across nested packet sections is rejected.
- Broker token, order language, private account balance, data ingestion, and
  generated-output requests are rejected.

## Boundary

Manual review packets remain docs/manual artifacts. They are not data files,
generated reports, trading signals, or execution workflows.
