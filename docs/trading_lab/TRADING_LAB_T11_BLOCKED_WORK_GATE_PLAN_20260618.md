# Trading Lab T11 Blocked-Work Gate Plan

Date: 2026-06-18

## Purpose

T11 adds a validation-only gate for future Trading Lab work requests. The gate
helps classify proposed work before it becomes code, data, app wiring, or
deployment. It does not approve any future blocked work.

## Classification

- `ALLOW_RESEARCH_ONLY`: manual paper/research docs, templates, examples, and
  validation-only hygiene.
- `HOLD_NEEDS_EXPLICIT_APPROVAL`: future-phase work that may be discussable only
  after a separate approval, such as data ingestion, backtesting implementation,
  simulation tooling, generated artifacts, app wiring, deployment, or CI/CD.
- `REJECT_PROHIBITED`: real-money trading, broker orders, broker/API
  integration, credentials, secrets, keys, tokens, private account data,
  automated execution, production investment advice, or fantasy-lane changes.

## Allowed T11 Work

- Add in-memory text classification helpers.
- Add fake-payload tests for HOLD and REJECT outcomes.
- Document the gate and remaining blocked areas.

## Not Allowed

- No data ingestion.
- No backtesting implementation.
- No broker/API integration.
- No credentials, secrets, keys, or tokens.
- No app or deployment wiring.
- No fantasy-football lane edits.
- No generated market datasets or outputs.

## Expected Result

Trading Lab should be able to screen future requests while keeping all execution,
broker, credential, data-ingestion, deployment, and fantasy-lane work blocked.
