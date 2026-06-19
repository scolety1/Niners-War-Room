# Trading Lab T10 Lifecycle Validation Plan

Date: 2026-06-18

## Purpose

T10 validates manual paper lifecycle states and transitions without creating an
execution workflow. Helpers operate on in-memory status strings and notes only.

## Covered States

- IDEA
- SOURCE_REVIEW
- WATCHLIST_NOTE
- RISK_REVIEW
- PAPER_JOURNAL_OPEN
- PAPER_REVIEW_DUE
- CLOSED_LESSONS
- REJECTED_PROHIBITED
- HOLD_NEEDS_REVIEW

## Boundary

No broker/API, credentials, real-money orders, auto-execution, private account
data, data ingestion, generated outputs, app wiring, or deployment.
