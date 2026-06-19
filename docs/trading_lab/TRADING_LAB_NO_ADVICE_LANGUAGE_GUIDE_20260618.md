# Trading Lab No-Advice Language Guide

Date: 2026-06-18

## Purpose

This guide helps operators keep Trading Lab notes research-only,
paper-only, and not investment advice. It does not approve trading,
execution, broker/API integration, credentials, deployment, or data ingestion.

## Safe Language

Use language like:

- Research question
- Paper-only hypothesis
- Manual review
- Invalidation condition
- Learning goal
- Public-source citation
- Risk note
- HOLD pending source review
- Closed lessons

## Prohibited Language

Avoid and reject language like:

- Buy now
- Sell now
- Place order
- Execute
- Guaranteed return
- Based on my brokerage balance
- Use my broker token
- Connect broker
- Auto-execute
- Real position sizing

## Rewrite Examples

| unsafe_language | safe_rewrite |
| --- | --- |
| Buy `EXMPL` now | Research question: what public evidence would support or weaken a paper-only hypothesis about `EXMPL`? |
| Sell now if it drops | Invalidation condition: close the paper note if the public evidence no longer supports the hypothesis. |
| Place stop-loss order | Risk note: describe the paper-only risk condition without broker orders. |
| Execute when threshold crosses | Manual review: mark the paper note for review if the hypothetical threshold is observed. |
| Guaranteed return | Learning goal: compare the hypothesis against public evidence and document uncertainty. |
| Based on my brokerage balance | Paper-only sizing hypothesis: use a fixed fictional unit with no account data. |
| Use my broker token | Source review: reject credential-dependent sources. |

## Safe Use Reminder

Trading Lab language should support learning, tracking, and manual paper review.
It must not instruct a reader to trade, use a broker, provide secrets, automate
execution, rely on private account data, or treat a note as production advice.
