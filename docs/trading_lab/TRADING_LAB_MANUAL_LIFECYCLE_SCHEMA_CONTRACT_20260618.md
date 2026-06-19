# Trading Lab Manual Lifecycle Schema Contract

Date: 2026-06-18

## Purpose

The manual lifecycle contract formalizes non-executing paper research states.
It is not a trading workflow, broker workflow, app workflow, or deployment
workflow.

## Allowed States

- `IDEA`
- `SOURCE_REVIEW`
- `RESEARCH_INTAKE`
- `WATCHLIST_NOTE`
- `STRATEGY_NOTE`
- `RISK_REVIEW`
- `PAPER_JOURNAL_OPEN`
- `PAPER_REVIEW_DUE`
- `CLOSED_LESSONS`
- `HOLD_NEEDS_REVIEW`
- `REJECTED_PROHIBITED`

## Valid Transitions

| from | to | condition |
| --- | --- | --- |
| `IDEA` | `RESEARCH_INTAKE` | Paper-only research question exists. |
| `RESEARCH_INTAKE` | `SOURCE_REVIEW` | Public source names are identified or HOLD is required. |
| `SOURCE_REVIEW` | `WATCHLIST_NOTE` | Sources pass public-source review. |
| `SOURCE_REVIEW` | `STRATEGY_NOTE` | Research question needs strategy-note framing. |
| `WATCHLIST_NOTE` | `RISK_REVIEW` | Hypothesis and invalidation notes exist. |
| `STRATEGY_NOTE` | `RISK_REVIEW` | Assumptions and risks are documented. |
| `RISK_REVIEW` | `PAPER_JOURNAL_OPEN` | No prohibited content is found. |
| `PAPER_JOURNAL_OPEN` | `PAPER_REVIEW_DUE` | Manual review date arrives. |
| `PAPER_REVIEW_DUE` | `CLOSED_LESSONS` | Lessons are captured without advice. |
| Any state | `HOLD_NEEDS_REVIEW` | Source, language, or policy question remains. |
| Any state | `REJECTED_PROHIBITED` | Prohibited content appears. |

## Invalid Transitions

- Any state to broker order placement
- Any state to broker/API connection
- Any state to credential or secret setup
- Any state to automated execution
- Any state to data ingestion or generated outputs
- Any state to deployment or app wiring
- Any state to fantasy-lane behavior

## Required Transition Fields

- `lifecycle_id`
- `from_status`
- `to_status`
- `transition_date`
- `operator`
- `transition_reason`
- `guardrail_check`
- `notes`
