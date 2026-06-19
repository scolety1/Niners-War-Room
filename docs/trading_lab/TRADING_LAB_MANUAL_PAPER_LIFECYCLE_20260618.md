# Trading Lab Manual Paper Lifecycle

Date: 2026-06-18

## Purpose

This lifecycle supports manual paper research. It is not an execution workflow,
broker workflow, data ingestion pipeline, deployment path, or investment-advice
process.

## Lifecycle Statuses

- `IDEA`
- `SOURCE_REVIEW`
- `WATCHLIST_NOTE`
- `RISK_REVIEW`
- `PAPER_JOURNAL_OPEN`
- `PAPER_REVIEW_DUE`
- `CLOSED_LESSONS`
- `REJECTED_PROHIBITED`
- `HOLD_NEEDS_REVIEW`

## Valid Transitions

| from | to | requirement |
| --- | --- | --- |
| `IDEA` | `SOURCE_REVIEW` | Research question is paper-only. |
| `SOURCE_REVIEW` | `WATCHLIST_NOTE` | Source is public or manually written and citeable. |
| `WATCHLIST_NOTE` | `RISK_REVIEW` | Risks and invalidation notes are present. |
| `RISK_REVIEW` | `PAPER_JOURNAL_OPEN` | No prohibited content found. |
| `PAPER_JOURNAL_OPEN` | `PAPER_REVIEW_DUE` | Review date arrives. |
| `PAPER_REVIEW_DUE` | `CLOSED_LESSONS` | Lessons are captured without advice. |
| Any status | `HOLD_NEEDS_REVIEW` | Terms, source policy, or language needs review. |
| Any status | `REJECTED_PROHIBITED` | Prohibited content appears. |

## Invalid Transitions

- Any transition to real order placement.
- Any transition requiring broker credentials.
- Any transition using an API key, token, secret, or `.env`.
- Any transition using private account data.
- Any auto-execution path.
- Any transition to deployment or app wiring.

## Fake Lifecycle Example

| lifecycle_id | status | note |
| --- | --- | --- |
| `LC-PAPER-001` | `IDEA` | Paper question about public filing attribution. |
| `LC-PAPER-001` | `SOURCE_REVIEW` | SEC EDGAR citation reviewed manually. |
| `LC-PAPER-001` | `WATCHLIST_NOTE` | Fictional `PAPER` symbol note drafted. |
| `LC-PAPER-001` | `RISK_REVIEW` | Thesis and source-quality risks reviewed. |
| `LC-PAPER-001` | `CLOSED_LESSONS` | Learned that source attribution improved note quality. |

## Safe Use Reminder

Lifecycle statuses describe manual research state only. They do not describe
trade states, orders, positions, account states, or execution status.
