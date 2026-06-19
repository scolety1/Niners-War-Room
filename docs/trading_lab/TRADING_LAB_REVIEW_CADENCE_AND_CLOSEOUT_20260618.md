# Trading Lab Review Cadence And Closeout

Date: 2026-06-18

## Purpose

This guide defines manual review cadence and closeout expectations for Trading
Lab paper research. It is not investment advice, real account guidance, broker
execution, deployment, or data ingestion.

## Recommended Cadence

| review_type | cadence | focus |
| --- | --- | --- |
| Intake review | At creation | Research question, paper-only intent, prohibited content. |
| Source review | Before citation | Public availability, attribution, terms, no credentials. |
| Watchlist review | Weekly while open | Hypothesis, public evidence, risk notes, invalidation. |
| Risk review | Before paper journal entry | Bias, source quality, process, advice-language drift. |
| Paper journal review | On review date | Lessons learned, invalidation, close/hold/reject. |
| Monthly lessons review | Monthly | Patterns in research process. |
| Quarterly lessons review | Quarterly | Guardrail quality and readiness gaps. |

## Closeout Checklist

- Source policy followed.
- No prohibited data.
- No execution path.
- No advice language.
- Risks reviewed.
- Invalidation conditions reviewed.
- Lessons captured.
- Status is `CLOSED_LESSONS`, `HOLD_NEEDS_REVIEW`, or
  `REJECTED_PROHIBITED`.
- No generated artifacts or raw data were created.

## Fake Closeout Example

| field | value |
| --- | --- |
| closeout_id | `CO-EXMPL-001` |
| paper_note | Fictional public filing watchlist note |
| source_policy_followed | Yes |
| prohibited_data_found | No |
| execution_path_found | No |
| advice_language_found | No |
| risks_reviewed | Thesis risk and source-quality risk |
| lessons | Public citation quality mattered more than the initial hypothesis. |
| status | `CLOSED_LESSONS` |

## Stop Conditions

Closeout must stop and mark `REJECTED_PROHIBITED` if it finds credentials,
private account data, broker/API dependencies, order language, automated
execution, deployment plans, generated outputs, or personalized advice.
